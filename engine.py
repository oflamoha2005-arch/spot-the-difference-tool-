import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def shift_color_precise(img_bgr, click_x=None, click_y=None, bbox=None, target_color_preset='green', custom_hue_shift=None, tolerance=14):
    """
    Shifts the color of the target object with outline-bounded precision.
    Features:
    - Smart seed refinement to snap away from black/dark outlines.
    - Barrier detection using dark outlines (gray < 52) & Canny edges.
    - Outline-aware floodfill preventing any color bleed into background/lawn/tables.
    - Box selection mode for complex/textured objects (dog, kite, characters).
    - Preserves dark outlines, shadows, and luminance for vibrant cartoon recoloring.
    """
    img_h, img_w = img_bgr.shape[:2]

    # Target preset hues in OpenCV HSV space (0-180)
    target_hues = {
        'green': 60,
        'yellow': 30,
        'blue': 115,
        'purple': 145,
        'orange': 16,
        'red': 0,
        'pink': 165,
        'cyan': 90
    }

    # 1. Determine ROI and Mode
    if bbox:
        bx, by, bw, bh = [int(v) for v in bbox]
        bx = max(0, min(bx, img_w - 1))
        by = max(0, min(by, img_h - 1))
        bw = max(2, min(bw, img_w - bx))
        bh = max(2, min(bh, img_h - by))

        pad = 8
        bx0 = max(0, bx - pad)
        by0 = max(0, by - pad)
        bx1 = min(img_w, bx + bw + pad)
        by1 = min(img_h, by + bh + pad)
        is_box_mode = True
        if click_x is None: click_x = bx + bw // 2
        if click_y is None: click_y = by + bh // 2
    else:
        is_box_mode = False
        click_x = max(0, min(int(click_x), img_w - 1))
        click_y = max(0, min(int(click_y), img_h - 1))
        radius = 160
        bx0 = max(0, click_x - radius)
        by0 = max(0, click_y - radius)
        bx1 = min(img_w, click_x + radius)
        by1 = min(img_h, click_y + radius)

    roi_bgr = img_bgr[by0:by1, bx0:bx1].copy()
    roi_h, roi_w = roi_bgr.shape[:2]
    roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)

    local_cx = max(0, min(click_x - bx0, roi_w - 1))
    local_cy = max(0, min(click_y - by0, roi_h - 1))

    # 2. Multi-scale Barrier Detection (Dark Outlines + Canny Edges)
    is_outline = (roi_gray < 52)
    edges = cv2.Canny(cv2.GaussianBlur(roi_gray, (3, 3), 0), 40, 110)
    barriers = cv2.bitwise_or(edges, (is_outline.astype(np.uint8) * 255))
    barriers_dil = cv2.dilate(barriers, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)))

    # 3. Intelligent Seed Refinement: snap away from dark outlines or barriers
    seed_x, seed_y = local_cx, local_cy
    if barriers_dil[local_cy, local_cx] > 0 or roi_hsv[local_cy, local_cx, 2] < 55:
        w_size = 6
        py0, py1 = max(0, local_cy - w_size), min(roi_h, local_cy + w_size + 1)
        px0, px1 = max(0, local_cx - w_size), min(roi_w, local_cx + w_size + 1)
        patch_barr = barriers_dil[py0:py1, px0:px1]
        patch_v = roi_hsv[py0:py1, px0:px1, 2]
        patch_s = roi_hsv[py0:py1, px0:px1, 1]

        valid_coords = np.argwhere((patch_barr == 0) & (patch_v > 60) & (patch_s > 30))
        if len(valid_coords) > 0:
            center = np.array([local_cy - py0, local_cx - px0])
            dists = np.sum((valid_coords - center)**2, axis=1)
            best = valid_coords[np.argmin(dists)]
            seed_y = py0 + best[0]
            seed_x = px0 + best[1]

    ref_hue = int(roi_hsv[seed_y, seed_x, 0])
    ref_sat = int(roi_hsv[seed_y, seed_x, 1])
    ref_val = int(roi_hsv[seed_y, seed_x, 2])

    if custom_hue_shift is not None:
        shift_val = int(custom_hue_shift) % 180
    else:
        target_hue = target_hues.get(target_color_preset.lower(), 60)
        shift_val = (target_hue - ref_hue) % 180

    # 4. Generate Object Mask
    if is_box_mode:
        # Box mode: strictly restricted within user's box
        user_mask = np.zeros((roi_h, roi_w), dtype=bool)
        ubx = max(0, bx - bx0)
        uby = max(0, by - by0)
        user_mask[uby:uby+bh, ubx:ubx+bw] = True

        h_chan = roi_hsv[:, :, 0].astype(int)
        s_chan = roi_hsv[:, :, 1].astype(int)
        v_chan = roi_hsv[:, :, 2].astype(int)
        h_dist = np.minimum(np.abs(h_chan - ref_hue), 180 - np.abs(h_chan - ref_hue))

        box_color_mask = user_mask & (h_dist <= tolerance) & (s_chan >= max(30, ref_sat - 65)) & (v_chan >= 55) & (~is_outline)
        final_mask = box_color_mask.astype(np.uint8) * 255
    else:
        # Click mode: Outline-bounded FloodFill
        flood_mask = np.zeros((roi_h + 2, roi_w + 2), np.uint8)
        flood_mask[1:roi_h+1, 1:roi_w+1] = (barriers_dil > 0).astype(np.uint8) * 1

        diff_limit = max(18, min(42, int(tolerance * 1.3)))
        flags = 4 | cv2.FLOODFILL_MASK_ONLY | (2 << 8)
        cv2.floodFill(
            roi_bgr.copy(),
            flood_mask,
            (seed_x, seed_y),
            newVal=(0, 0, 255),
            loDiff=(diff_limit, diff_limit, diff_limit),
            upDiff=(diff_limit, diff_limit, diff_limit),
            flags=flags
        )
        filled_pixels = (flood_mask[1:roi_h+1, 1:roi_w+1] == 2).astype(np.uint8) * 255

        cnts, _ = cv2.findContours(filled_pixels, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts) > 0 and cv2.contourArea(cnts[0]) >= 8:
            final_mask = np.zeros_like(filled_pixels)
            cv2.drawContours(final_mask, cnts, -1, 255, -1)
            # Expand slightly to touch inner black outline without halo
            final_mask = cv2.dilate(final_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)))
            final_mask[roi_gray < 50] = 0
        else:
            final_mask = filled_pixels

    # 5. Recoloring: Rotate Hue & enhance saturation while strictly preserving Value/shading
    shifted_hsv = roi_hsv.copy()
    mask_bool = final_mask > 0
    shifted_hsv[mask_bool, 0] = (shifted_hsv[mask_bool, 0].astype(int) + shift_val) % 180
    shifted_hsv[mask_bool, 1] = np.clip(shifted_hsv[mask_bool, 1].astype(int) + 20, 0, 255).astype(np.uint8)

    shifted_bgr = cv2.cvtColor(shifted_hsv, cv2.COLOR_HSV2BGR)

    # Soft alpha blend for anti-aliasing
    soft_mask = cv2.GaussianBlur(final_mask.astype(float) / 255.0, (3, 3), 0)[:, :, np.newaxis]
    blended = (shifted_bgr * soft_mask + roi_bgr * (1.0 - soft_mask)).astype(np.uint8)

    result = img_bgr.copy()
    result[by0:by1, bx0:bx1] = blended

    # 6. Calculate Bounding Box and Solution Metadata
    nonzero_y, nonzero_x = np.nonzero(final_mask)
    if len(nonzero_x) > 0:
        eff_bx = bx0 + int(np.min(nonzero_x))
        eff_by = by0 + int(np.min(nonzero_y))
        eff_bw = int(np.max(nonzero_x) - np.min(nonzero_x))
        eff_bh = int(np.max(nonzero_y) - np.min(nonzero_y))
        center_x = eff_bx + eff_bw // 2
        center_y = eff_by + eff_bh // 2
        radius = max(eff_bw, eff_bh) // 2 + 15
    else:
        center_x = click_x
        center_y = click_y
        radius = 35
        eff_bx, eff_by, eff_bw, eff_bh = click_x - 30, click_y - 30, 60, 60

    diff_meta = {
        "type": "color",
        "label": f"Changed color to {target_color_preset}",
        "center": [int(center_x), int(center_y)],
        "radius": int(radius),
        "bbox": [int(eff_bx), int(eff_by), int(eff_bw), int(eff_bh)]
    }
    return result, diff_meta

def erase_with_mask(img_bgr, mask_img_grayscale, inpaint_radius=None):
    """
    Erases pixels where mask > 0 with smart background healing.
    Eliminates dark outlines, color smearing, and starburst artifacts
    by sampling the true surrounding background and softly blending it seamlessly.
    Protects neighboring structural outlines from being eroded or smudged.
    """
    img_h, img_w = img_bgr.shape[:2]
    # Ensure mask has same dimensions
    if mask_img_grayscale.shape[:2] != (img_h, img_w):
        mask_img_grayscale = cv2.resize(mask_img_grayscale, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
    
    nonzero_y, nonzero_x = np.nonzero(mask_img_grayscale)
    if len(nonzero_x) == 0:
        return img_bgr.copy(), {
            "type": "erase",
            "label": "Removed item",
            "center": [0, 0],
            "radius": 20,
            "bbox": [0, 0, 10, 10]
        }

    bx = int(np.min(nonzero_x))
    by = int(np.min(nonzero_y))
    bw = int(np.max(nonzero_x) - np.min(nonzero_x))
    bh = int(np.max(nonzero_y) - np.min(nonzero_y))
    cx = bx + bw // 2
    cy = by + bh // 2
    radius = max(bw, bh) // 2 + 15

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Identify dark structural lines OUTSIDE the user's painted mask.
    # These belong to neighboring objects (roof eaves, tables, characters) and must NEVER be eroded or smudged.
    is_outer_dark = (gray < 52) & (mask_img_grayscale == 0)

    # Adaptive dilation: swallows the object's own black outlines and anti-aliasing fringes
    dilate_px = max(4, min(14, int(min(bw, bh) * 0.08) + 4))
    dilate_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1))
    clean_mask = cv2.dilate(mask_img_grayscale, dilate_k, iterations=1)
    
    # Strictly prevent the dilated mask from encroaching into outer structural outlines
    clean_mask[is_outer_dark] = 0

    # Surrounding border ring to sample the local background
    ring_w = max(10, min(25, dilate_px * 2))
    outer_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ((dilate_px + ring_w) * 2 + 1, (dilate_px + ring_w) * 2 + 1))
    outer_mask = cv2.dilate(clean_mask, outer_k, iterations=1)
    ring = cv2.subtract(outer_mask, clean_mask)
    # Exclude dark outlines from background color sampling
    ring[gray < 52] = 0

    ring_pixels = img_bgr[ring > 0]
    if len(ring_pixels) < 15:
        # Near edge fallback
        rad = inpaint_radius or max(5, dilate_px)
        result = cv2.inpaint(img_bgr, clean_mask, inpaintRadius=rad, flags=cv2.INPAINT_TELEA)
    else:
        ring_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)[ring > 0]
        
        # Check for white / neutral background (very common in cartoon walls, skies, etc.)
        is_neutral = (ring_hsv[:, 1] < 45) & (ring_hsv[:, 2] > 155)
        neutral_ratio = np.mean(is_neutral)

        if neutral_ratio >= 0.22:
            # Neutral / white wall background
            selected_pixels = ring_pixels[is_neutral]
            bg_color = np.median(selected_pixels, axis=0).astype(np.float32)
            bg_std = np.mean(np.std(selected_pixels, axis=0))
        else:
            # Chromatic background (e.g. blue sky, green grass, solid yellow)
            # Filter out dark outline pixels
            val_filter = ring_hsv[:, 2] >= 45
            cand_hsv = ring_hsv[val_filter] if np.sum(val_filter) > 15 else ring_hsv
            cand_bgr = ring_pixels[val_filter] if np.sum(val_filter) > 15 else ring_pixels

            # Cluster dominant Hue
            hues = cand_hsv[:, 0]
            hist, bins = np.histogram(hues, bins=18, range=(0, 180))
            dom_bin = np.argmax(hist)
            dom_min, dom_max = bins[dom_bin], bins[dom_bin + 1]

            bg_select = (cand_hsv[:, 0] >= dom_min) & (cand_hsv[:, 0] <= dom_max)
            if np.sum(bg_select) >= 10:
                bg_pixels = cand_bgr[bg_select]
            else:
                bg_pixels = cand_bgr
            bg_color = np.median(bg_pixels, axis=0).astype(np.float32)
            bg_std = np.mean(np.std(bg_pixels, axis=0))

        # Solid or smooth background (flat cartoon fill, sky, wall, grass)
        if bg_std < 50:
            pad = ring_w + dilate_px + 6
            roi_x0 = max(0, bx - pad)
            roi_y0 = max(0, by - pad)
            roi_x1 = min(img_w, bx + bw + pad)
            roi_y1 = min(img_h, by + bh + pad)

            roi_mask = clean_mask[roi_y0:roi_y1, roi_x0:roi_x1]
            roi_img = img_bgr[roi_y0:roi_y1, roi_x0:roi_x1].copy()
            rh, rw = roi_img.shape[:2]

            bg_fill_roi = np.full((rh, rw, 3), bg_color, dtype=np.float32)

            blur_k = max(5, (dilate_px // 2) * 2 + 1)
            alpha = cv2.GaussianBlur(roi_mask.astype(np.float32) / 255.0, (blur_k, blur_k), 0)
            alpha_3d = np.repeat(alpha[:, :, np.newaxis], 3, axis=2)

            blended_roi = (roi_img.astype(np.float32) * (1.0 - alpha_3d) + bg_fill_roi * alpha_3d).astype(np.uint8)

            # Re-enforce external dark outlines in the ROI so neighboring objects remain crisp
            roi_gray = gray[roi_y0:roi_y1, roi_x0:roi_x1]
            roi_outer_dark = (roi_gray < 52) & (mask_img_grayscale[roi_y0:roi_y1, roi_x0:roi_x1] == 0)
            blended_roi[roi_outer_dark] = roi_img[roi_outer_dark]

            result = img_bgr.copy()
            result[roi_y0:roi_y1, roi_x0:roi_x1] = blended_roi
        else:
            # Complex textured background: use Navier-Stokes with adaptive radius
            rad = inpaint_radius or max(5, min(20, int(min(bw, bh) * 0.12)))
            result = cv2.inpaint(img_bgr, clean_mask, inpaintRadius=rad, flags=cv2.INPAINT_NS)

    diff_meta = {
        "type": "erase",
        "label": "Removed item",
        "center": [int(cx), int(cy)],
        "radius": int(radius),
        "bbox": [int(bx), int(by), int(bw), int(bh)]
    }
    return result, diff_meta

def flip_selection(img_bgr, bbox):
    """
    Flips a selection horizontally.
    """
    bx, by, bw, bh = [int(v) for v in bbox]
    img_h, img_w = img_bgr.shape[:2]
    bx = max(0, min(bx, img_w - 1))
    by = max(0, min(by, img_h - 1))
    bw = max(2, min(bw, img_w - bx))
    bh = max(2, min(bh, img_h - by))

    result = img_bgr.copy()
    patch = result[by:by+bh, bx:bx+bw]
    result[by:by+bh, bx:bx+bw] = cv2.flip(patch, 1)

    diff_meta = {
        "type": "flip",
        "label": "Flipped direction",
        "center": [int(bx + bw // 2), int(by + bh // 2)],
        "radius": int(max(bw, bh) // 2 + 15),
        "bbox": [bx, by, bw, bh]
    }
    return result, diff_meta

def clone_element(img_bgr, src_bbox, dest_center, blend_mode="seamless"):
    """
    Clones/duplicates an object from src_bbox and pastes it at dest_center [x, y].
    Uses OpenCV seamlessClone with automatic feathered fallback.
    """
    img_h, img_w = img_bgr.shape[:2]
    sx, sy, sw, sh = [int(v) for v in src_bbox]
    sx = max(0, min(sx, img_w - 2))
    sy = max(0, min(sy, img_h - 2))
    sw = max(4, min(sw, img_w - sx))
    sh = max(4, min(sh, img_h - sy))

    patch = img_bgr[sy:sy+sh, sx:sx+sw]
    dcx, dcy = int(dest_center[0]), int(dest_center[1])

    # Clamp center so seamlessClone won't assert error
    min_cx = sw // 2 + 2
    max_cx = img_w - sw // 2 - 2
    min_cy = sh // 2 + 2
    max_cy = img_h - sh // 2 - 2

    result = img_bgr.copy()
    success = False

    if blend_mode == "seamless" and min_cx < max_cx and min_cy < max_cy and sw >= 8 and sh >= 8:
        safe_cx = max(min_cx, min(max_cx, dcx))
        safe_cy = max(min_cy, min(max_cy, dcy))
        mask = 255 * np.ones((sh, sw), dtype=np.uint8)
        # Soften edges of mask
        cv2.rectangle(mask, (0, 0), (sw - 1, sh - 1), 0, 2)
        try:
            result = cv2.seamlessClone(patch, img_bgr, mask, (safe_cx, safe_cy), cv2.NORMAL_CLONE)
            dcx, dcy = safe_cx, safe_cy
            success = True
        except Exception:
            success = False

    if not success:
        # High quality feathered direct blend
        dx = max(0, min(img_w - sw, dcx - sw // 2))
        dy = max(0, min(img_h - sh, dcy - sh // 2))
        
        feather_mask = np.zeros((sh, sw), dtype=np.float32)
        cv2.ellipse(feather_mask, (sw // 2, sh // 2), (max(1, sw // 2 - 2), max(1, sh // 2 - 2)), 0, 0, 360, 1.0, -1)
        feather_mask = cv2.GaussianBlur(feather_mask, (5, 5), 0)
        feather_3d = np.repeat(feather_mask[:, :, np.newaxis], 3, axis=2)

        target_roi = result[dy:dy+sh, dx:dx+sw]
        blended = (patch * feather_3d + target_roi * (1.0 - feather_3d)).astype(np.uint8)
        result[dy:dy+sh, dx:dx+sw] = blended
        dcx, dcy = dx + sw // 2, dy + sh // 2

    diff_meta = {
        "type": "clone",
        "label": "Duplicated item (Added object)",
        "center": [int(dcx), int(dcy)],
        "radius": int(max(sw, sh) // 2 + 15),
        "bbox": [int(dcx - sw // 2), int(dcy - sh // 2), int(sw), int(sh)]
    }
    return result, diff_meta

def draw_solution_image(img_bgr, differences):
    """
    Draws neat, high-visibility red/coral circles with badges on the solution image.
    """
    sol = img_bgr.copy()
    img_h, img_w = sol.shape[:2]

    # Convert to PIL for anti-aliased circles and text rendering
    pil_img = Image.fromarray(cv2.cvtColor(sol, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img, "RGBA")

    # Try loading a clear font, otherwise fallback
    try:
        font = ImageFont.truetype("arial.ttf", size=max(18, img_w // 40))
    except:
        font = ImageFont.load_default()

    for idx, diff in enumerate(differences, 1):
        cx, cy = diff["center"]
        r = diff.get("radius", 35)

        # Draw outer white border + vibrant red circle
        x0, y0 = cx - r, cy - r
        x1, y1 = cx + r, cy + r

        # White contrast outline (width 6)
        draw.ellipse([x0-2, y0-2, x1+2, y1+2], outline=(255, 255, 255, 220), width=6)
        # Red/Coral circle (width 4)
        draw.ellipse([x0, y0, x1, y1], outline=(255, 59, 48, 255), width=4)

        # Number Badge at top-right of the circle
        badge_r = max(14, r // 3)
        bx, by = cx + int(r * 0.707), cy - int(r * 0.707)
        # Badge background
        draw.ellipse([bx - badge_r - 2, by - badge_r - 2, bx + badge_r + 2, by + badge_r + 2], fill=(255, 255, 255, 255))
        draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=(255, 59, 48, 255))
        # Number text
        text = str(idx)
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((bx - tw / 2, by - th / 2 - 2), text, fill=(255, 255, 255, 255), font=font)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def create_kdp_puzzle_page(img_a_bgr, img_b_bgr, num_diffs=5, title="CAN YOU SPOT THE DIFFERENCES?", page_num=1, page_size="8.5x8.5"):
    """
    Assembles a print-ready 300 DPI page for Amazon KDP.
    Default 8.5 x 8.5 inches = 2550 x 2550 px at 300 DPI.
    """
    if page_size == "8.5x11":
        PAGE_W, PAGE_H = 2550, 3300
    else:  # 8.5x8.5 square
        PAGE_W, PAGE_H = 2550, 2550

    # Create white canvas
    page = Image.new("RGB", (PAGE_W, PAGE_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(page)

    # Fonts
    try:
        title_font = ImageFont.truetype("arialbd.ttf", size=70)
        subtitle_font = ImageFont.truetype("arial.ttf", size=42)
        tag_font = ImageFont.truetype("arialbd.ttf", size=36)
        page_font = ImageFont.truetype("arial.ttf", size=32)
    except:
        title_font = subtitle_font = tag_font = page_font = ImageFont.load_default()

    # Draw decorative top border
    draw.rectangle([80, 70, PAGE_W - 80, 80], fill=(240, 240, 245))

    # Title text
    full_title = f"{title}" if title else f"SPOT THE {num_diffs} DIFFERENCES!"
    t_bbox = draw.textbbox((0, 0), full_title, font=title_font)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text(((PAGE_W - t_w) // 2, 110), full_title, fill=(30, 41, 59), font=title_font)

    # Subtitle with instructions
    sub_text = f"Look closely at the two pictures below. Can you find all {num_diffs} differences?"
    s_bbox = draw.textbbox((0, 0), sub_text, font=subtitle_font)
    s_w = s_bbox[2] - s_bbox[0]
    draw.text(((PAGE_W - s_w) // 2, 195), sub_text, fill=(100, 116, 139), font=subtitle_font)

    # Layout: Top/Bottom images
    # Calculate image slots
    avail_h = PAGE_H - 420 - 150
    spacing = 50
    img_box_h = (avail_h - spacing) // 2
    img_box_w = min(int(img_box_h * 1.15), PAGE_W - 240)

    # Convert BGR to RGB PIL
    pil_a = Image.fromarray(cv2.cvtColor(img_a_bgr, cv2.COLOR_BGR2RGB))
    pil_b = Image.fromarray(cv2.cvtColor(img_b_bgr, cv2.COLOR_BGR2RGB))

    # Resize preserving aspect ratio
    pil_a.thumbnail((img_box_w, img_box_h), Image.Resampling.LANCZOS)
    pil_b.thumbnail((img_box_w, img_box_h), Image.Resampling.LANCZOS)

    # Position 1: Image A (Top)
    x_a = (PAGE_W - pil_a.width) // 2
    y_a = 265
    # Shadow/Border for Image A
    draw.rectangle([x_a - 4, y_a - 4, x_a + pil_a.width + 4, y_a + pil_a.height + 4], outline=(203, 213, 225), width=3)
    page.paste(pil_a, (x_a, y_a))

    # Tag for Image A
    tag_a = "PICTURE 1"
    draw.rounded_rectangle([x_a + 15, y_a + 15, x_a + 180, y_a + 60], radius=8, fill=(30, 41, 59))
    draw.text((x_a + 30, y_a + 22), tag_a, fill=(255, 255, 255), font=tag_font)

    # Position 2: Image B (Bottom)
    x_b = (PAGE_W - pil_b.width) // 2
    y_b = y_a + pil_a.height + spacing
    # Shadow/Border for Image B
    draw.rectangle([x_b - 4, y_b - 4, x_b + pil_b.width + 4, y_b + pil_b.height + 4], outline=(203, 213, 225), width=3)
    page.paste(pil_b, (x_b, y_b))

    # Tag for Image B
    tag_b = "PICTURE 2"
    draw.rounded_rectangle([x_b + 15, y_b + 15, x_b + 180, y_b + 60], radius=8, fill=(239, 68, 68))
    draw.text((x_b + 30, y_b + 22), tag_b, fill=(255, 255, 255), font=tag_font)

    # Bottom Checklist area (Circles for kid to check off as they find each difference)
    checklist_y = y_b + pil_b.height + 35
    circle_r = 20
    box_gap = 130
    total_boxes_w = num_diffs * box_gap
    start_box_x = (PAGE_W - total_boxes_w) // 2

    for i in range(num_diffs):
        bx = start_box_x + i * box_gap + 40
        by = checklist_y + circle_r
        # Draw check circle
        draw.ellipse([bx - circle_r, by - circle_r, bx + circle_r, by + circle_r], outline=(148, 163, 184), width=3)
        # Number label
        lbl = f"#{i+1}"
        draw.text((bx + circle_r + 10, by - 16), lbl, fill=(71, 85, 105), font=tag_font)

    # Page number at the very bottom
    p_text = f"- {page_num} -"
    pb = draw.textbbox((0, 0), p_text, font=page_font)
    draw.text(((PAGE_W - (pb[2]-pb[0])) // 2, PAGE_H - 70), p_text, fill=(148, 163, 184), font=page_font)

    return page

def create_kdp_solution_page(img_sol_bgr, differences, page_num="SOLUTIONS", page_size="8.5x8.5"):
    """
    Creates the solution page showing circled image and list of differences.
    """
    if page_size == "8.5x11":
        PAGE_W, PAGE_H = 2550, 3300
    else:
        PAGE_W, PAGE_H = 2550, 2550

    page = Image.new("RGB", (PAGE_W, PAGE_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(page)

    try:
        title_font = ImageFont.truetype("arialbd.ttf", size=72)
        sub_font = ImageFont.truetype("arial.ttf", size=40)
        item_font = ImageFont.truetype("arial.ttf", size=36)
        num_font = ImageFont.truetype("arialbd.ttf", size=36)
    except:
        title_font = sub_font = item_font = num_font = ImageFont.load_default()

    # Title
    draw.text((PAGE_W // 2 - 200, 100), "SOLUTIONS KEY", fill=(239, 68, 68), font=title_font)
    draw.text((PAGE_W // 2 - 250, 185), f"Here are the {len(differences)} differences revealed!", fill=(100, 116, 139), font=sub_font)

    # Solution Image
    pil_sol = Image.fromarray(cv2.cvtColor(img_sol_bgr, cv2.COLOR_BGR2RGB))
    max_img_h = 1350
    max_img_w = PAGE_W - 300
    pil_sol.thumbnail((max_img_w, max_img_h), Image.Resampling.LANCZOS)

    x = (PAGE_W - pil_sol.width) // 2
    y = 260
    draw.rectangle([x - 5, y - 5, x + pil_sol.width + 5, y + pil_sol.height + 5], outline=(203, 213, 225), width=4)
    page.paste(pil_sol, (x, y))

    # List of differences at the bottom
    list_y = y + pil_sol.height + 60
    draw.text((220, list_y), "Differences List:", fill=(30, 41, 59), font=num_font)
    list_y += 55

    for idx, diff in enumerate(differences, 1):
        col_x = 220 if idx <= 4 else PAGE_W // 2 + 50
        row_y = list_y + ((idx - 1) % 4) * 55
        
        # Badge
        draw.ellipse([col_x, row_y, col_x + 36, row_y + 36], fill=(239, 68, 68))
        draw.text((col_x + 11, row_y + 4), str(idx), fill=(255, 255, 255), font=num_font)
        # Description
        label = diff.get("label", f"Difference #{idx}")
        draw.text((col_x + 55, row_y + 4), label, fill=(51, 65, 85), font=item_font)

    return page
