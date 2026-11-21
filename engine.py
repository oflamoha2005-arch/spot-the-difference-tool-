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

    # Scalable high-visibility line width and contrast outline
    line_w = max(8, int(img_w / 140))
    contrast_w = line_w + 6
    offset = (contrast_w - line_w) // 2

    # Try loading a bold font for the badge
    font_candidates = [
        r'c:\Users\DELL\Desktop\train game\fonts\Poppins-Bold.ttf',
        r'C:\Windows\Fonts\arialbd.ttf',
        r'C:\Windows\Fonts\segoeuib.ttf'
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    for idx, diff in enumerate(differences, 1):
        cx, cy = diff["center"]
        r = diff.get("radius", 35)

        # Draw outer pure white contrast outline + bold vibrant red circle
        x0, y0 = cx - r, cy - r
        x1, y1 = cx + r, cy + r

        # White contrast outline for maximum visibility on all backgrounds
        draw.ellipse([x0 - offset, y0 - offset, x1 + offset, y1 + offset], outline=(255, 255, 255, 255), width=contrast_w)
        # Bold vibrant red circle
        draw.ellipse([x0, y0, x1, y1], outline=(230, 18, 18, 255), width=line_w)

        # Number Badge at top-right of the circle
        badge_r = max(20, int(r * 0.42))
        bx, by = cx + int(r * 0.707), cy - int(r * 0.707)

        badge_font_size = max(20, int(badge_r * 1.25))
        if font_path:
            try:
                b_font = ImageFont.truetype(font_path, size=badge_font_size)
            except Exception:
                b_font = ImageFont.load_default()
        else:
            b_font = ImageFont.load_default()

        # White border + Red Badge fill
        draw.ellipse([bx - badge_r - 3, by - badge_r - 3, bx + badge_r + 3, by + badge_r + 3], fill=(255, 255, 255, 255))
        draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=(230, 18, 18, 255))

        # Centered number text
        text = str(idx)
        bbox = draw.textbbox((0, 0), text, font=b_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((bx - tw / 2, by - th / 2 - 2), text, fill=(255, 255, 255, 255), font=b_font)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def create_kdp_puzzle_page(img_a_bgr, img_b_bgr, num_diffs=5, title="CAN YOU SPOT THE DIFFERENCES?", page_num=1, page_size="8.5x8.5", show_tags=False):
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

    # Tag for Image A (hidden by default so it never obscures any differences)
    if show_tags:
        tag_a = "PICTURE 1"
        draw.rounded_rectangle([x_a + 15, y_a + 15, x_a + 180, y_a + 60], radius=8, fill=(30, 41, 59))
        draw.text((x_a + 30, y_a + 22), tag_a, fill=(255, 255, 255), font=tag_font)

    # Position 2: Image B (Bottom)
    x_b = (PAGE_W - pil_b.width) // 2
    y_b = y_a + pil_a.height + spacing
    # Shadow/Border for Image B
    draw.rectangle([x_b - 4, y_b - 4, x_b + pil_b.width + 4, y_b + pil_b.height + 4], outline=(203, 213, 225), width=3)
    page.paste(pil_b, (x_b, y_b))

    # Tag for Image B (hidden by default so it never obscures any differences)
    if show_tags:
        tag_b = "PICTURE 2"
        draw.rounded_rectangle([x_b + 15, y_b + 15, x_b + 180, y_b + 60], radius=8, fill=(239, 68, 68))
        draw.text((x_b + 30, y_b + 22), tag_b, fill=(255, 255, 255), font=tag_font)

    # Bottom Checklist area (Circles for kid to check off as they find each difference)
    checklist_y = y_b + pil_b.height + 30
    circle_r = 18
    # Dynamic box gap so any number of differences fits cleanly without overflow
    max_avail_w = PAGE_W - 240
    box_gap = min(130, max(75, max_avail_w // max(1, num_diffs)))
    total_boxes_w = num_diffs * box_gap
    start_box_x = (PAGE_W - total_boxes_w) // 2

    for i in range(num_diffs):
        bx = start_box_x + i * box_gap + (box_gap // 4)
        by = checklist_y + circle_r
        # Draw check circle
        draw.ellipse([bx - circle_r, by - circle_r, bx + circle_r, by + circle_r], outline=(148, 163, 184), width=3)
        # Number label
        lbl = f"#{i+1}"
        draw.text((bx + circle_r + 8, by - 14), lbl, fill=(71, 85, 105), font=tag_font)

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

    half = (len(differences) + 1) // 2
    for idx, diff in enumerate(differences, 1):
        col_x = 220 if idx <= half else PAGE_W // 2 + 50
        row_idx = (idx - 1) if idx <= half else (idx - 1 - half)
        row_y = list_y + row_idx * 55

        # Badge
        draw.ellipse([col_x, row_y, col_x + 36, row_y + 36], fill=(239, 68, 68))
        draw.text((col_x + 11, row_y + 4), str(idx), fill=(255, 255, 255), font=num_font)
        # Description
        label = diff.get("label", f"Difference #{idx}")
        draw.text((col_x + 55, row_y + 4), label, fill=(51, 65, 85), font=item_font)

    return page

def get_kdp_font(name='body', size=36, bold=False):
    """
    Robust font loader prioritizing high-quality system fonts on Windows/Linux/macOS.
    """
    windir = os.environ.get('WINDIR', 'C:\\Windows')
    font_files = {
        'title': ['arialbd.ttf', 'segoeuib.ttf', 'calibrib.ttf'],
        'bold': ['arialbd.ttf', 'segoeuib.ttf', 'calibrib.ttf'],
        'body': ['arial.ttf', 'segoeui.ttf', 'calibri.ttf'],
        'comic': ['comicbd.ttf' if bold else 'comic.ttf', 'arialbd.ttf' if bold else 'arial.ttf']
    }
    candidates = font_files.get(name, ['arialbd.ttf' if bold else 'arial.ttf'])
    for cand in candidates:
        win_path = os.path.join(windir, 'Fonts', cand)
        if os.path.exists(win_path):
            try:
                return ImageFont.truetype(win_path, size=size)
            except Exception:
                pass
        try:
            return ImageFont.truetype(cand, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def create_kdp_belongs_to_page(title="SPOT THE DIFFERENCE", page_size="8.5x8.5"):
    """
    Creates an attractive 'This Book Belongs To' intro page for Amazon KDP activity books.
    """
    PAGE_W, PAGE_H = (2550, 3300) if page_size == "8.5x11" else (2550, 2550)
    page = Image.new("RGB", (PAGE_W, PAGE_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(page)

    margin = 120
    draw.rounded_rectangle([margin, margin, PAGE_W - margin, PAGE_H - margin], radius=30, outline=(226, 232, 240), width=6)
    draw.rounded_rectangle([margin + 18, margin + 18, PAGE_W - margin - 18, PAGE_H - margin - 18], radius=24, outline=(148, 163, 184), width=2)

    for cx, cy in [(margin + 60, margin + 60), (PAGE_W - margin - 60, margin + 60),
                   (margin + 60, PAGE_H - margin - 60), (PAGE_W - margin - 60, PAGE_H - margin - 60)]:
        draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(239, 68, 68))
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(255, 255, 255))

    tag_font = get_kdp_font('bold', 38)
    tag_text = "FUN & CHALLENGING ACTIVITY BOOK"
    tb = draw.textbbox((0, 0), tag_text, font=tag_font)
    tw = tb[2] - tb[0]
    tag_y = margin + 140
    draw.rounded_rectangle([(PAGE_W - tw) // 2 - 30, tag_y - 12, (PAGE_W + tw) // 2 + 30, tag_y + 50], radius=12, fill=(241, 245, 249))
    draw.text(((PAGE_W - tw) // 2, tag_y), tag_text, fill=(71, 85, 105), font=tag_font)

    title_font = get_kdp_font('title', 92)
    t1 = title.upper()
    tb1 = draw.textbbox((0, 0), t1, font=title_font)
    draw.text(((PAGE_W - (tb1[2] - tb1[0])) // 2, tag_y + 110), t1, fill=(15, 23, 42), font=title_font)

    sub_font = get_kdp_font('bold', 50)
    t2 = "ACTIVITY PUZZLE BOOK FOR KIDS"
    tb2 = draw.textbbox((0, 0), t2, font=sub_font)
    draw.text(((PAGE_W - (tb2[2] - tb2[0])) // 2, tag_y + 235), t2, fill=(239, 68, 68), font=sub_font)

    div_y = tag_y + 350
    draw.line([(PAGE_W // 2 - 300), div_y, (PAGE_W // 2 + 300), div_y], fill=(203, 213, 225), width=4)

    mag_y = div_y + 190
    mag_r = 105
    draw.ellipse([PAGE_W // 2 - mag_r - 40, mag_y - mag_r, PAGE_W // 2 + mag_r - 40, mag_y + mag_r], outline=(30, 41, 59), width=18)
    draw.ellipse([PAGE_W // 2 - mag_r - 30, mag_y - mag_r + 10, PAGE_W // 2 + mag_r - 50, mag_y + mag_r - 10], outline=(148, 163, 184), width=6)
    draw.line([PAGE_W // 2 + int(mag_r * 0.6) - 40, mag_y + int(mag_r * 0.6), PAGE_W // 2 + mag_r + 90, mag_y + mag_r + 130], fill=(30, 41, 59), width=28)

    box_y = mag_y + 270
    box_w = 1600
    box_h = 360
    bx0 = (PAGE_W - box_w) // 2
    bx1 = bx0 + box_w
    draw.rounded_rectangle([bx0, box_y, bx1, box_y + box_h], radius=24, outline=(203, 213, 225), width=4, fill=(248, 250, 252))

    lbl_font = get_kdp_font('bold', 48)
    lbl_text = "THIS BOOK BELONGS TO:"
    lbb = draw.textbbox((0, 0), lbl_text, font=lbl_font)
    draw.text(((PAGE_W - (lbb[2] - lbb[0])) // 2, box_y + 60), lbl_text, fill=(30, 41, 59), font=lbl_font)

    line_y = box_y + 230
    draw.line([bx0 + 120, line_y, bx1 - 120, line_y], fill=(148, 163, 184), width=4)

    msg_font = get_kdp_font('body', 38)
    m1 = "Sharpen your focus, train your eyes, and have fun finding all the hidden differences!"
    mb1 = draw.textbbox((0, 0), m1, font=msg_font)
    draw.text(((PAGE_W - (mb1[2] - mb1[0])) // 2, box_y + box_h + 120), m1, fill=(100, 116, 139), font=msg_font)

    return page

def create_kdp_instructions_page(page_size="8.5x8.5"):
    """
    Creates an instructions page (How to Play) for Amazon KDP activity books.
    """
    PAGE_W, PAGE_H = (2550, 3300) if page_size == "8.5x11" else (2550, 2550)
    page = Image.new("RGB", (PAGE_W, PAGE_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(page)

    margin = 120
    draw.rounded_rectangle([margin, margin, PAGE_W - margin, PAGE_H - margin], radius=30, outline=(226, 232, 240), width=6)
    draw.rounded_rectangle([margin + 18, margin + 18, PAGE_W - margin - 18, PAGE_H - margin - 18], radius=24, outline=(148, 163, 184), width=2)

    t_font = get_kdp_font('title', 82)
    t = "HOW TO PLAY"
    tb = draw.textbbox((0, 0), t, font=t_font)
    draw.text(((PAGE_W - (tb[2] - tb[0])) // 2, margin + 100), t, fill=(30, 41, 59), font=t_font)

    sub_font = get_kdp_font('bold', 42)
    sub = "Become a Master Detective in 4 Simple Steps!"
    sb = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(((PAGE_W - (sb[2] - sb[0])) // 2, margin + 210), sub, fill=(239, 68, 68), font=sub_font)

    draw.line([PAGE_W // 2 - 250, margin + 290, PAGE_W // 2 + 250, margin + 290], fill=(203, 213, 225), width=4)

    steps = [
        ("1", "Look Closely at the Two Pictures",
         "Picture 1 is at the top, and Picture 2 is at the bottom. At first glance they look identical, but small sneaky changes are hidden!"),
        ("2", "Spot Every Difference",
         "Search carefully for changes: a swapped color, a missing bird or cloud, a flipped item, or a newly added object!"),
        ("3", "Circle and Track Your Score",
         "Whenever you find a difference, circle it with your pencil and check off the tracker circle at the bottom of the page!"),
        ("4", "Check Your Answers at the Back",
         "Stuck on a tricky puzzle? Turn to the Solutions Key at the back of the book to reveal all numbered badges and locations!")
    ]

    card_y = margin + 350
    card_w = PAGE_W - (margin * 2) - 160
    card_x = (PAGE_W - card_w) // 2
    step_num_font = get_kdp_font('bold', 44)
    step_title_font = get_kdp_font('bold', 40)
    step_desc_font = get_kdp_font('body', 34)

    for num, stitle, sdesc in steps:
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + 220], radius=20, fill=(248, 250, 252), outline=(226, 232, 240), width=3)
        badge_cx, badge_cy = card_x + 70, card_y + 110
        draw.ellipse([badge_cx - 45, badge_cy - 45, badge_cx + 45, badge_cy + 45], fill=(239, 68, 68))
        nb = draw.textbbox((0, 0), num, font=step_num_font)
        draw.text((badge_cx - (nb[2] - nb[0]) // 2, badge_cy - (nb[3] - nb[1]) // 2 - 2), num, fill=(255, 255, 255), font=step_num_font)

        draw.text((card_x + 145, card_y + 35), stitle, fill=(30, 41, 59), font=step_title_font)
        draw.text((card_x + 145, card_y + 95), sdesc, fill=(100, 116, 139), font=step_desc_font)
        card_y += 260

    tip_y = card_y + 30
    draw.rounded_rectangle([card_x, tip_y, card_x + card_w, tip_y + 180], radius=16, fill=(254, 242, 242), outline=(254, 202, 202), width=3)
    tip_title_font = get_kdp_font('bold', 36)
    tip_text_font = get_kdp_font('body', 32)
    draw.text((card_x + 50, tip_y + 35), "DETECTIVE PRO TIP:", fill=(220, 38, 38), font=tip_title_font)
    draw.text((card_x + 50, tip_y + 90), "Scan each scene systematically in a grid: sky first, then background, then main characters!", fill=(127, 29, 29), font=tip_text_font)

    cr_font = get_kdp_font('body', 28)
    cr = "All Rights Reserved. High-Resolution 300 DPI Amazon KDP Activity Book Edition."
    crb = draw.textbbox((0, 0), cr, font=cr_font)
    draw.text(((PAGE_W - (crb[2] - crb[0])) // 2, PAGE_H - margin - 40), cr, fill=(148, 163, 184), font=cr_font)

    return page

def create_kdp_certificate_page(page_size="8.5x8.5"):
    """
    Creates an official Master Detective completion certificate for kids.
    """
    PAGE_W, PAGE_H = (2550, 3300) if page_size == "8.5x11" else (2550, 2550)
    page = Image.new("RGB", (PAGE_W, PAGE_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(page)

    margin = 120
    draw.rounded_rectangle([margin, margin, PAGE_W - margin, PAGE_H - margin], radius=32, outline=(245, 158, 11), width=8)
    draw.rounded_rectangle([margin + 20, margin + 20, PAGE_W - margin - 20, PAGE_H - margin - 20], radius=24, outline=(30, 41, 59), width=3)

    t_font = get_kdp_font('title', 90)
    t = "CERTIFICATE"
    tb = draw.textbbox((0, 0), t, font=t_font)
    draw.text(((PAGE_W - (tb[2] - tb[0])) // 2, margin + 140), t, fill=(30, 41, 59), font=t_font)

    sub_font = get_kdp_font('bold', 48)
    sub = "OF COMPLETION & MASTER DETECTIVE STATUS"
    sb = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(((PAGE_W - (sb[2] - sb[0])) // 2, margin + 260), sub, fill=(245, 158, 11), font=sub_font)

    draw.line([PAGE_W // 2 - 350, margin + 350, PAGE_W // 2 + 350, margin + 350], fill=(226, 232, 240), width=4)

    pres_font = get_kdp_font('body', 42)
    p_text = "This award is proudly presented to:"
    pb = draw.textbbox((0, 0), p_text, font=pres_font)
    draw.text(((PAGE_W - (pb[2] - pb[0])) // 2, margin + 460), p_text, fill=(100, 116, 139), font=pres_font)

    name_line_y = margin + 700
    draw.line([margin + 250, name_line_y, PAGE_W - margin - 250, name_line_y], fill=(30, 41, 59), width=6)
    name_hint = "( Detective's Name )"
    nh_font = get_kdp_font('body', 32)
    nhb = draw.textbbox((0, 0), name_hint, font=nh_font)
    draw.text(((PAGE_W - (nhb[2] - nhb[0])) // 2, name_line_y + 25), name_hint, fill=(148, 163, 184), font=nh_font)

    desc_font = get_kdp_font('body', 40)
    d1 = "For outstanding observational skills, sharp focus, and perseverance"
    d2 = "in successfully finding all hidden differences across the entire book!"
    db1 = draw.textbbox((0, 0), d1, font=desc_font)
    db2 = draw.textbbox((0, 0), d2, font=desc_font)
    draw.text(((PAGE_W - (db1[2] - db1[0])) // 2, margin + 870), d1, fill=(51, 65, 85), font=desc_font)
    draw.text(((PAGE_W - (db2[2] - db2[0])) // 2, margin + 940), d2, fill=(51, 65, 85), font=desc_font)

    medal_cx, medal_cy = PAGE_W // 2, margin + 1240
    draw.ellipse([medal_cx - 100, medal_cy - 100, medal_cx + 100, medal_cy + 100], fill=(245, 158, 11))
    draw.ellipse([medal_cx - 85, medal_cy - 85, medal_cx + 85, medal_cy + 85], fill=(255, 255, 255))
    star_font = get_kdp_font('bold', 70)
    st = "★"
    stb = draw.textbbox((0, 0), st, font=star_font)
    draw.text((medal_cx - (stb[2] - stb[0]) // 2, medal_cy - (stb[3] - stb[1]) // 2 - 5), st, fill=(245, 158, 11), font=star_font)

    sig_y = margin + 1600
    draw.line([margin + 200, sig_y, margin + 750, sig_y], fill=(148, 163, 184), width=4)
    draw.line([PAGE_W - margin - 750, sig_y, PAGE_W - margin - 200, sig_y], fill=(148, 163, 184), width=4)
    s_lbl_font = get_kdp_font('bold', 34)
    draw.text((margin + 380, sig_y + 20), "DATE", fill=(100, 116, 139), font=s_lbl_font)
    draw.text((PAGE_W - margin - 570, sig_y + 20), "OFFICIAL SEAL / SIGNATURE", fill=(100, 116, 139), font=s_lbl_font)

    return page

def create_kdp_multi_solution_page(solutions_batch, page_size="8.5x8.5", page_num=None):
    """
    Creates a 4-solutions-per-page (2x2 grid) solution key page for Amazon KDP books.
    solutions_batch: list of up to 4 dicts:
      [
        {
          "puzzle_num": 1,
          "sol_bgr": <numpy bgr image with circles>,
          "diff_count": 5,
          "differences": [...]
        }, ...
      ]
    """
    PAGE_W, PAGE_H = (2550, 3300) if page_size == "8.5x11" else (2550, 2550)
    page = Image.new("RGB", (PAGE_W, PAGE_H), color=(255, 255, 255))
    draw = ImageDraw.Draw(page)

    title_font = get_kdp_font('title', 70)
    sub_font = get_kdp_font('body', 38)
    p_num_font = get_kdp_font('bold', 34)
    item_font = get_kdp_font('body', 28)

    p_nums = [s.get("puzzle_num", i+1) for i, s in enumerate(solutions_batch)]
    title_text = "SOLUTIONS KEY"
    tb = draw.textbbox((0, 0), title_text, font=title_font)
    draw.text(((PAGE_W - (tb[2] - tb[0])) // 2, 75), title_text, fill=(239, 68, 68), font=title_font)

    range_str = f"Puzzles {p_nums[0]} - {p_nums[-1]}" if len(p_nums) > 1 else f"Puzzle {p_nums[0]}"
    sub_text = f"Check your answers below for {range_str}"
    sb = draw.textbbox((0, 0), sub_text, font=sub_font)
    draw.text(((PAGE_W - (sb[2] - sb[0])) // 2, 160), sub_text, fill=(100, 116, 139), font=sub_font)

    margin_x = 100
    top_y = 230
    bottom_y = PAGE_H - 100
    grid_w = PAGE_W - (margin_x * 2)
    grid_h = bottom_y - top_y
    gap = 40

    cell_w = (grid_w - gap) // 2
    cell_h = (grid_h - gap) // 2

    for idx, sol_item in enumerate(solutions_batch):
        if idx >= 4:
            break
        r = idx // 2
        c = idx % 2
        cx = margin_x + c * (cell_w + gap)
        cy = top_y + r * (cell_h + gap)

        draw.rounded_rectangle([cx, cy, cx + cell_w, cy + cell_h], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=3)

        p_num = sol_item.get("puzzle_num", idx + 1)
        diff_cnt = sol_item.get("diff_count", len(sol_item.get("differences", [])))
        badge_w = 260
        draw.rounded_rectangle([cx + 25, cy + 20, cx + 25 + badge_w, cy + 70], radius=8, fill=(30, 41, 59))
        p_lbl = f"PUZZLE #{p_num}"
        plb = draw.textbbox((0, 0), p_lbl, font=p_num_font)
        draw.text((cx + 25 + (badge_w - (plb[2] - plb[0])) // 2, cy + 27), p_lbl, fill=(255, 255, 255), font=p_num_font)

        cnt_lbl = f"({diff_cnt} Differences)"
        draw.text((cx + 300, cy + 30), cnt_lbl, fill=(100, 116, 139), font=sub_font)

        sol_bgr = sol_item.get("sol_bgr")
        if sol_bgr is not None:
            pil_sol = Image.fromarray(cv2.cvtColor(sol_bgr, cv2.COLOR_BGR2RGB))
            max_img_w = cell_w - 50
            max_img_h = cell_h - 180
            pil_sol.thumbnail((max_img_w, max_img_h), Image.Resampling.LANCZOS)

            img_x = cx + (cell_w - pil_sol.width) // 2
            img_y = cy + 85
            draw.rectangle([img_x - 3, img_y - 3, img_x + pil_sol.width + 3, img_y + pil_sol.height + 3], outline=(203, 213, 225), width=2)
            page.paste(pil_sol, (img_x, img_y))

            ft_y = img_y + pil_sol.height + 15
            summary_txt = f"All {diff_cnt} differences circled & numbered above"
            stb = draw.textbbox((0, 0), summary_txt, font=item_font)
            draw.text((cx + (cell_w - (stb[2] - stb[0])) // 2, ft_y), summary_txt, fill=(71, 85, 105), font=item_font)

    if page_num is not None:
        pn_font = get_kdp_font('body', 32)
        pn_text = f"- {page_num} -"
        pnb = draw.textbbox((0, 0), pn_text, font=pn_font)
        draw.text(((PAGE_W - (pnb[2] - pnb[0])) // 2, PAGE_H - 70), pn_text, fill=(148, 163, 184), font=pn_font)

    return page

def compile_full_kdp_book(
    puzzles_list,
    output_pdf_path,
    title="SPOT THE DIFFERENCES",
    page_size="8.5x8.5",
    include_belongs_to=True,
    include_instructions=True,
    include_certificate=True,
    solutions_per_page=4
):
    """
    Compiles all puzzles into a professional 300 DPI Amazon KDP Activity Book PDF.
    - Front matter: Belongs-To Page + How to Play Instructions
    - Section 1: All Puzzle Pages (Sequential 1..N)
    - Section 2: Solutions Key (4-in-1 grid)
    - Back matter: Certificate of Completion
    """
    pages = []
    current_page_num = 1

    # 1. Front Matter: Belongs To Page
    if include_belongs_to:
        p_belongs = create_kdp_belongs_to_page(title=title, page_size=page_size)
        pages.append(p_belongs)
        current_page_num += 1

    # 2. Front Matter: Instructions Page
    if include_instructions:
        p_instr = create_kdp_instructions_page(page_size=page_size)
        pages.append(p_instr)
        current_page_num += 1

    # 3. Puzzles Section
    solutions_data = []
    for idx, p in enumerate(puzzles_list, 1):
        orig_bgr = p.get("original_bgr")
        mod_bgr = p.get("current_bgr")
        diffs = p.get("differences", [])
        p_title = p.get("title", f"CAN YOU SPOT THE {len(diffs)} DIFFERENCES?")

        puzzle_page = create_kdp_puzzle_page(
            orig_bgr,
            mod_bgr,
            num_diffs=len(diffs),
            title=p_title,
            page_num=current_page_num,
            page_size=page_size
        )
        pages.append(puzzle_page)
        current_page_num += 1

        # Prepare solution data
        sol_bgr = draw_solution_image(mod_bgr, diffs)
        solutions_data.append({
            "puzzle_num": idx,
            "sol_bgr": sol_bgr,
            "diff_count": len(diffs),
            "differences": diffs
        })

    # 4. Solutions Section
    if solutions_per_page == 4:
        for i in range(0, len(solutions_data), 4):
            batch = solutions_data[i:i+4]
            sol_page = create_kdp_multi_solution_page(batch, page_size=page_size, page_num=current_page_num)
            pages.append(sol_page)
            current_page_num += 1
    else:
        for item in solutions_data:
            sol_page = create_kdp_solution_page(item["sol_bgr"], item["differences"], page_num=current_page_num, page_size=page_size)
            pages.append(sol_page)
            current_page_num += 1

    # 5. Back Matter: Certificate
    if include_certificate:
        p_cert = create_kdp_certificate_page(page_size=page_size)
        pages.append(p_cert)

    # Save to 300 DPI PDF
    if pages:
        pages[0].save(
            output_pdf_path,
            "PDF",
            resolution=300.0,
            save_all=True,
            append_images=pages[1:]
        )
    return output_pdf_path

