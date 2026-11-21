"""
Script to build Christmas Spot the Difference KDP Book pages and PDFs.
Removes 'PICTURE 1' and 'PICTURE 2' badge overlays from top of the images
so they never obscure or cover differences in the top-left or any part of the artwork.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = os.path.join(BASE_DIR, 'Christmas_SpotTheDifference_50_Scenes_FIXED', 'Christmas_SpotTheDifference')
OUT_DIR = os.path.join(BASE_DIR, 'outputs', 'kdp_preview_samples')
TMPL_PUZZLE = os.path.join(BASE_DIR, 'scratch', 'template_assets', 'puzzle_template_hi_res.png')
TMPL_AK = os.path.join(BASE_DIR, 'scratch', 'template_assets', 'answer_key_hi_res.png')
SPECIAL_DIR = os.path.join(BASE_DIR, 'scratch', 'special_pages')

os.makedirs(OUT_DIR, exist_ok=True)

# Frame coordinates inside the master SVG template (1898 x 2530)
P1_BOX = (136, 434, 1626, 842)  # x, y, w, h
P2_BOX = (136, 1292, 1626, 842) # x, y, w, h

def make_puzzle_page(orig_bgr, mod_bgr, puzzle_tmpl):
    """
    Overlays Picture 1 (Original) and Picture 2 (Modified) into the Christmas template.
    NO 'PICTURE 1' or 'PICTURE 2' badges are overlaid on top of the images,
    leaving 100% of the artwork visible with zero obstruction for differences.
    """
    page = puzzle_tmpl.copy()
    target_w, target_h = P1_BOX[2], P1_BOX[3]

    orig_res = cv2.resize(orig_bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    mod_res = cv2.resize(mod_bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

    # 1. Overlay Picture 1
    page[P1_BOX[1]:P1_BOX[1]+target_h, P1_BOX[0]:P1_BOX[0]+target_w] = orig_res
    cv2.rectangle(page, (P1_BOX[0], P1_BOX[1]), (P1_BOX[0]+target_w, P1_BOX[1]+target_h), (25, 25, 25), 4)

    # 2. Overlay Picture 2
    page[P2_BOX[1]:P2_BOX[1]+target_h, P2_BOX[0]:P2_BOX[0]+target_w] = mod_res
    cv2.rectangle(page, (P2_BOX[0], P2_BOX[1]), (P2_BOX[0]+target_w, P2_BOX[1]+target_h), (25, 25, 25), 4)

    # Note: Badge overlays (PICTURE 1 / PICTURE 2) are intentionally omitted
    # so they do not cover any differences!

    return page

def build_sample_puzzles():
    puzzle_tmpl = cv2.imread(TMPL_PUZZLE)
    assert puzzle_tmpl is not None, f"Could not load puzzle template from {TMPL_PUZZLE}"

    scene_files = ['Scene_01.webp', 'Scene_02.webp', 'Scene_03.webp', 'Scene_04.webp']
    puzzles_data = []

    for idx, sf in enumerate(scene_files, 1):
        sp = os.path.join(SCENES_DIR, sf)
        orig = cv2.imread(sp)
        assert orig is not None, f"Could not load scene {sf}"
        oh, ow = orig.shape[:2]

        # 5 sample differences for preview
        mod = orig.copy()
        diffs = [
            {'id': 1, 'center': [int(ow * 0.22), int(oh * 0.32)], 'radius': 60, 'label': f'Diff 1 (P{idx})'},
            {'id': 2, 'center': [int(ow * 0.75), int(oh * 0.25)], 'radius': 55, 'label': f'Diff 2 (P{idx})'},
            {'id': 3, 'center': [int(ow * 0.18), int(oh * 0.72)], 'radius': 65, 'label': f'Diff 3 (P{idx})'},
            {'id': 4, 'center': [int(ow * 0.82), int(oh * 0.68)], 'radius': 70, 'label': f'Diff 4 (P{idx})'},
            {'id': 5, 'center': [int(ow * 0.50), int(oh * 0.80)], 'radius': 60, 'label': f'Diff 5 (P{idx})'}
        ]

        for d in diffs:
            cx, cy = d['center']
            r = d['radius']
            roi = mod[max(0, cy-r):min(oh, cy+r), max(0, cx-r):min(ow, cx+r)]
            if roi.shape[0] > 0 and roi.shape[1] > 0:
                if d['id'] % 2 == 0:
                    mod[max(0, cy-r):min(oh, cy+r), max(0, cx-r):min(ow, cx+r)] = cv2.flip(roi, 1)
                else:
                    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                    hsv[:, :, 0] = (hsv[:, :, 0].astype(int) + 60) % 180
                    mod[max(0, cy-r):min(oh, cy+r), max(0, cx-r):min(ow, cx+r)] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        page_bgr = make_puzzle_page(orig, mod, puzzle_tmpl)
        sol_bgr = engine.draw_solution_image(mod, diffs)

        puzzles_data.append({
            'num': idx,
            'page_bgr': page_bgr,
            'sol_bgr': sol_bgr,
            'diffs': diffs
        })

    return puzzles_data

def build_all():
    print("Building clean Christmas puzzle pages without PICTURE 1 / PICTURE 2 overlays...")
    puzzles = build_sample_puzzles()

    # Save 4 clean puzzle pages
    puzzle_imgs = []
    for p in puzzles:
        num = p['num']
        pil_p = Image.fromarray(cv2.cvtColor(p['page_bgr'], cv2.COLOR_BGR2RGB))
        p_path = os.path.join(OUT_DIR, f'template_page_{num}.png')
        pil_p.save(p_path)
        puzzle_imgs.append(pil_p)
        print(f"  -> Saved {p_path} (No PICTURE 1/2 overlay)")

    # Solution page 5 (4-in-1 answer key)
    page5_path = os.path.join(OUT_DIR, 'template_page_5.png')
    page5_pil = Image.open(page5_path)

    # 1. Compile 5-page sample PDF
    sample_pdf = os.path.join(OUT_DIR, 'Christmas_SpotTheDifference_Sample_Book.pdf')
    puzzle_imgs[0].save(sample_pdf, 'PDF', resolution=300.0, save_all=True, append_images=puzzle_imgs[1:] + [page5_pil])
    print(f"Compiled 5-page Sample PDF: {sample_pdf} ({os.path.getsize(sample_pdf)} bytes)")

    # 2. Compile full 8-page Master Book Structure
    thank_you_page = os.path.join(OUT_DIR, 'page_thank_you.png')
    if not os.path.exists(thank_you_page):
        thank_you_page = os.path.join(OUT_DIR, 'page_follow_us.png')

    pages_order = [
        os.path.join(OUT_DIR, 'page_belongs_to.png'),
        os.path.join(OUT_DIR, 'page_welcome.png'),
        os.path.join(OUT_DIR, 'template_page_1.png'),
        os.path.join(OUT_DIR, 'template_page_2.png'),
        os.path.join(OUT_DIR, 'template_page_3.png'),
        os.path.join(OUT_DIR, 'template_page_4.png'),
        os.path.join(OUT_DIR, 'template_page_5.png'),
        thank_you_page
    ]

    all_pil = [Image.open(p) for p in pages_order if os.path.exists(p)]
    if len(all_pil) == 8:
        full_pdf = os.path.join(OUT_DIR, 'Christmas_SpotTheDifference_Complete_Book_Structure.pdf')
        all_pil[0].save(full_pdf, 'PDF', resolution=300.0, save_all=True, append_images=all_pil[1:])
        print(f"Compiled Complete 8-page Book PDF: {full_pdf} ({os.path.getsize(full_pdf)} bytes)")

    print("All builds completed successfully!")

if __name__ == '__main__':
    build_all()
