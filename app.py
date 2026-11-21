import os
import cv2
import json
import base64
import shutil
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import engine
import prompt_engine

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
BOOK_FOLDER = os.path.join(OUTPUT_FOLDER, 'book')
BOOK_PUZZLES_DIR = os.path.join(BOOK_FOLDER, 'puzzles')
BOOK_CONFIG_FILE = os.path.join(BOOK_FOLDER, 'book.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(BOOK_PUZZLES_DIR, exist_ok=True)

# In-Memory Book & Active State
BOOK = {
    "title": "CAN YOU SPOT THE DIFFERENCES?",
    "page_size": "8.5x8.5",
    "include_belongs_to": True,
    "include_instructions": True,
    "include_certificate": True,
    "solutions_per_page": 4,
    "target_differences": 5,
    "only_completed_in_pdf": True,
    "active_id": 1,
    "puzzles": []
}

STATE = {
    "puzzle_id": 1,
    "title": "Puzzle 1",
    "original_bgr": None,
    "current_bgr": None,
    "history": [],
    "differences": [],
    "image_name": "sample_park.jpg",
    "image_url": "/static/samples/sample_park.jpg",
    "modified_url": "/outputs/current_modified.png"
}

def save_book_config():
    data = {
        "title": BOOK["title"],
        "page_size": BOOK["page_size"],
        "include_belongs_to": BOOK["include_belongs_to"],
        "include_instructions": BOOK["include_instructions"],
        "include_certificate": BOOK["include_certificate"],
        "solutions_per_page": BOOK["solutions_per_page"],
        "target_differences": BOOK.get("target_differences", 5),
        "only_completed_in_pdf": BOOK.get("only_completed_in_pdf", True),
        "active_id": BOOK["active_id"],
        "puzzles": [
            {
                "id": p["id"],
                "title": p.get("title", f"Puzzle {p['id']}"),
                "dir_name": p["dir_name"],
                "diff_count": p.get("diff_count", 0)
            } for p in BOOK["puzzles"]
        ]
    }
    with open(BOOK_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_active_puzzle():
    pid = STATE["puzzle_id"]
    p_info = next((p for p in BOOK["puzzles"] if p["id"] == pid), None)
    if not p_info:
        return
    p_dir = os.path.join(BOOK_PUZZLES_DIR, p_info["dir_name"])
    os.makedirs(p_dir, exist_ok=True)

    if STATE["current_bgr"] is not None:
        mod_path = os.path.join(p_dir, 'modified.png')
        cv2.imwrite(mod_path, STATE["current_bgr"])
        # Update output preview
        cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), STATE["current_bgr"])

        # Update Thumbnail
        th, tw = STATE["current_bgr"].shape[:2]
        scale = 220.0 / max(th, tw)
        thumb = cv2.resize(STATE["current_bgr"], (int(tw * scale), int(th * scale)))
        cv2.imwrite(os.path.join(p_dir, 'thumb.png'), thumb)

    diff_path = os.path.join(p_dir, 'differences.json')
    with open(diff_path, 'w', encoding='utf-8') as f:
        json.dump(STATE["differences"], f, indent=2, ensure_ascii=False)

    p_info["diff_count"] = len(STATE["differences"])
    save_book_config()

def load_puzzle(puzzle_id):
    p_info = next((p for p in BOOK["puzzles"] if p["id"] == puzzle_id), None)
    if not p_info:
        if BOOK["puzzles"]:
            p_info = BOOK["puzzles"][0]
            puzzle_id = p_info["id"]
        else:
            return False

    p_dir = os.path.join(BOOK_PUZZLES_DIR, p_info["dir_name"])
    orig_path = os.path.join(p_dir, 'original.png')
    mod_path = os.path.join(p_dir, 'modified.png')
    diff_path = os.path.join(p_dir, 'differences.json')

    if not os.path.exists(orig_path):
        return False

    orig_bgr = cv2.imread(orig_path)
    mod_bgr = cv2.imread(mod_path) if os.path.exists(mod_path) else orig_bgr.copy()

    diffs = []
    if os.path.exists(diff_path):
        try:
            with open(diff_path, 'r', encoding='utf-8') as f:
                diffs = json.load(f)
        except Exception:
            diffs = []

    STATE["puzzle_id"] = puzzle_id
    STATE["title"] = p_info.get("title", f"Puzzle {puzzle_id}")
    STATE["original_bgr"] = orig_bgr
    STATE["current_bgr"] = mod_bgr
    STATE["differences"] = diffs
    STATE["history"] = []
    STATE["image_url"] = f"/api/book/puzzle/{puzzle_id}/image/original"
    STATE["modified_url"] = f"/api/book/puzzle/{puzzle_id}/image/modified"

    # Also sync current_modified.png in outputs for instant view
    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), mod_bgr)

    BOOK["active_id"] = puzzle_id
    save_book_config()
    return True

def init_book():
    if os.path.exists(BOOK_CONFIG_FILE):
        try:
            with open(BOOK_CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            BOOK["title"] = cfg.get("title", "CAN YOU SPOT THE DIFFERENCES?")
            BOOK["page_size"] = cfg.get("page_size", "8.5x8.5")
            BOOK["include_belongs_to"] = cfg.get("include_belongs_to", True)
            BOOK["include_instructions"] = cfg.get("include_instructions", True)
            BOOK["include_certificate"] = cfg.get("include_certificate", True)
            BOOK["solutions_per_page"] = cfg.get("solutions_per_page", 4)
            BOOK["target_differences"] = cfg.get("target_differences", 5)
            BOOK["only_completed_in_pdf"] = cfg.get("only_completed_in_pdf", True)
            BOOK["puzzles"] = cfg.get("puzzles", [])
            active_id = cfg.get("active_id", 1)
            if BOOK["puzzles"]:
                load_puzzle(active_id)
                return
        except Exception as e:
            print("Notice: Starting new book session (config reload:", e, ")")

    # Initialize default sample park puzzle
    sample_path = os.path.join(os.path.dirname(__file__), 'static', 'samples', 'sample_park.jpg')
    if os.path.exists(sample_path):
        p1_dir = os.path.join(BOOK_PUZZLES_DIR, 'puzzle_01')
        os.makedirs(p1_dir, exist_ok=True)
        shutil.copyfile(sample_path, os.path.join(p1_dir, 'original.png'))
        shutil.copyfile(sample_path, os.path.join(p1_dir, 'modified.png'))

        bgr = cv2.imread(sample_path)
        th, tw = bgr.shape[:2]
        scale = 220.0 / max(th, tw)
        thumb = cv2.resize(bgr, (int(tw * scale), int(th * scale)))
        cv2.imwrite(os.path.join(p1_dir, 'thumb.png'), thumb)

        with open(os.path.join(p1_dir, 'differences.json'), 'w', encoding='utf-8') as f:
            json.dump([], f)

        BOOK["puzzles"] = [{
            "id": 1,
            "title": "Puzzle 1 (Park Scene)",
            "dir_name": "puzzle_01",
            "diff_count": 0
        }]
        BOOK["active_id"] = 1
        load_puzzle(1)

init_book()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/api/state', methods=['GET'])
def get_state():
    target = BOOK.get("target_differences", 5)
    total = len(BOOK["puzzles"])
    completed_count = sum(1 for p in BOOK["puzzles"] if p.get("diff_count", 0) >= target)
    pending_count = total - completed_count
    progress_pct = int((completed_count / total) * 100) if total > 0 else 0

    puzzles_summary = []
    for p in BOOK["puzzles"]:
        d_cnt = p.get("diff_count", 0)
        puzzles_summary.append({
            "id": p["id"],
            "title": p.get("title", f"Puzzle {p['id']}"),
            "diff_count": d_cnt,
            "is_completed": d_cnt >= target,
            "is_active": p["id"] == BOOK["active_id"],
            "thumb_url": f"/api/book/puzzle/{p['id']}/image/thumb?t={os.urandom(3).hex()}"
        })

    active_diff_cnt = len(STATE["differences"])
    active_is_completed = active_diff_cnt >= target

    return jsonify({
        "book": {
            "title": BOOK["title"],
            "page_size": BOOK["page_size"],
            "include_belongs_to": BOOK["include_belongs_to"],
            "include_instructions": BOOK["include_instructions"],
            "include_certificate": BOOK["include_certificate"],
            "solutions_per_page": BOOK["solutions_per_page"],
            "target_differences": target,
            "only_completed_in_pdf": BOOK.get("only_completed_in_pdf", True),
            "total_puzzles": total,
            "completed_count": completed_count,
            "pending_count": pending_count,
            "progress_percent": progress_pct,
            "all_completed": total > 0 and completed_count == total,
            "active_id": BOOK["active_id"]
        },
        "puzzles": puzzles_summary,
        "active_puzzle": {
            "id": STATE["puzzle_id"],
            "title": STATE["title"],
            "differences_count": active_diff_cnt,
            "target_differences": target,
            "is_completed": active_is_completed,
            "differences": STATE["differences"],
            "has_undo": len(STATE["history"]) > 0,
            "image_url": f"/api/book/puzzle/{STATE['puzzle_id']}/image/original?t={os.urandom(3).hex()}",
            "modified_url": f"/api/book/puzzle/{STATE['puzzle_id']}/image/modified?t={os.urandom(3).hex()}"
        },
        # Direct bindings for active canvas
        "image_url": f"/api/book/puzzle/{STATE['puzzle_id']}/image/original?t={os.urandom(3).hex()}",
        "modified_url": f"/api/book/puzzle/{STATE['puzzle_id']}/image/modified?t={os.urandom(3).hex()}",
        "differences_count": active_diff_cnt,
        "target_differences": target,
        "is_completed": active_is_completed,
        "differences": STATE["differences"],
        "has_undo": len(STATE["history"]) > 0
    })

@app.route('/api/book/state', methods=['GET'])
def get_book_state():
    return get_state()

@app.route('/api/book/select-puzzle', methods=['POST'])
def select_puzzle():
    data = request.json or {}
    puzzle_id = int(data.get('puzzle_id', 1))
    save_active_puzzle()
    success = load_puzzle(puzzle_id)
    if not success:
        return jsonify({"error": f"Failed to load puzzle {puzzle_id}"}), 404
    return get_state()

@app.route('/api/book/next-pending', methods=['POST'])
def next_pending_puzzle():
    save_active_puzzle()
    target = BOOK.get("target_differences", 5)
    current_id = STATE["puzzle_id"]
    puzzles = BOOK["puzzles"]
    if not puzzles:
        return get_state()

    # Find pending puzzles (diff_count < target)
    pending_puzzles = [p for p in puzzles if p.get("diff_count", 0) < target]
    if not pending_puzzles:
        # All are completed! Stay on current but state indicates all_completed
        return get_state()

    curr_idx = next((i for i, p in enumerate(puzzles) if p["id"] == current_id), -1)

    # Search for next pending puzzle after current_idx
    next_p = None
    for p in puzzles[curr_idx + 1:]:
        if p.get("diff_count", 0) < target:
            next_p = p
            break

    # If no pending puzzle after current, wrap around to first pending
    if not next_p:
        next_p = pending_puzzles[0]

    load_puzzle(next_p["id"])
    return get_state()

@app.route('/api/book/prev-puzzle', methods=['POST'])
def prev_puzzle():
    save_active_puzzle()
    current_id = STATE["puzzle_id"]
    puzzles = BOOK["puzzles"]
    if not puzzles:
        return get_state()

    curr_idx = next((i for i, p in enumerate(puzzles) if p["id"] == current_id), 0)
    prev_idx = (curr_idx - 1) % len(puzzles)
    load_puzzle(puzzles[prev_idx]["id"])
    return get_state()

@app.route('/api/book/upload-batch', methods=['POST'])
def upload_batch():
    files = request.files.getlist('files')
    if not files:
        if 'file' in request.files:
            files = [request.files['file']]
        else:
            return jsonify({"error": "No files uploaded"}), 400

    new_ids = []
    for f in files:
        if not f.filename:
            continue
        filename = secure_filename(f.filename)
        max_id = max([p["id"] for p in BOOK["puzzles"]], default=0)
        new_id = max_id + 1
        dir_name = f"puzzle_{new_id:02d}"
        p_dir = os.path.join(BOOK_PUZZLES_DIR, dir_name)
        os.makedirs(p_dir, exist_ok=True)

        temp_path = os.path.join(p_dir, 'temp_' + filename)
        f.save(temp_path)
        bgr = cv2.imread(temp_path)
        if bgr is None:
            shutil.rmtree(p_dir, ignore_errors=True)
            continue
        try:
            os.remove(temp_path)
        except Exception:
            pass

        orig_path = os.path.join(p_dir, 'original.png')
        mod_path = os.path.join(p_dir, 'modified.png')
        cv2.imwrite(orig_path, bgr)
        cv2.imwrite(mod_path, bgr)

        th, tw = bgr.shape[:2]
        scale = 220.0 / max(th, tw)
        thumb = cv2.resize(bgr, (int(tw * scale), int(th * scale)))
        cv2.imwrite(os.path.join(p_dir, 'thumb.png'), thumb)

        with open(os.path.join(p_dir, 'differences.json'), 'w', encoding='utf-8') as df:
            json.dump([], df)

        clean_name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        p_item = {
            "id": new_id,
            "title": f"Puzzle {new_id} ({clean_name[:22]})",
            "dir_name": dir_name,
            "diff_count": 0
        }
        BOOK["puzzles"].append(p_item)
        new_ids.append(new_id)

    if new_ids:
        save_active_puzzle()
        load_puzzle(new_ids[0])
    save_book_config()
    return get_state()

@app.route('/api/book/add-sample', methods=['POST'])
def add_sample_puzzle():
    sample_path = os.path.join(os.path.dirname(__file__), 'static', 'samples', 'sample_park.jpg')
    if not os.path.exists(sample_path):
        return jsonify({"error": "Sample file not found"}), 404

    max_id = max([p["id"] for p in BOOK["puzzles"]], default=0)
    new_id = max_id + 1
    dir_name = f"puzzle_{new_id:02d}"
    p_dir = os.path.join(BOOK_PUZZLES_DIR, dir_name)
    os.makedirs(p_dir, exist_ok=True)

    shutil.copyfile(sample_path, os.path.join(p_dir, 'original.png'))
    shutil.copyfile(sample_path, os.path.join(p_dir, 'modified.png'))

    bgr = cv2.imread(sample_path)
    th, tw = bgr.shape[:2]
    scale = 220.0 / max(th, tw)
    thumb = cv2.resize(bgr, (int(tw * scale), int(th * scale)))
    cv2.imwrite(os.path.join(p_dir, 'thumb.png'), thumb)

    with open(os.path.join(p_dir, 'differences.json'), 'w', encoding='utf-8') as df:
        json.dump([], df)

    p_item = {
        "id": new_id,
        "title": f"Puzzle {new_id} (Park Scene)",
        "dir_name": dir_name,
        "diff_count": 0
    }
    BOOK["puzzles"].append(p_item)
    save_active_puzzle()
    load_puzzle(new_id)
    save_book_config()
    return get_state()

@app.route('/api/book/delete-puzzle', methods=['POST'])
def delete_puzzle():
    data = request.json or {}
    puzzle_id = int(data.get('puzzle_id', 0))
    if len(BOOK["puzzles"]) <= 1:
        return jsonify({"error": "Cannot delete the only puzzle in the book"}), 400

    idx = next((i for i, p in enumerate(BOOK["puzzles"]) if p["id"] == puzzle_id), None)
    if idx is None:
        return jsonify({"error": "Puzzle not found"}), 404

    p_info = BOOK["puzzles"].pop(idx)
    p_dir = os.path.join(BOOK_PUZZLES_DIR, p_info["dir_name"])
    shutil.rmtree(p_dir, ignore_errors=True)

    if BOOK["active_id"] == puzzle_id:
        new_active = BOOK["puzzles"][min(idx, len(BOOK["puzzles"]) - 1)]["id"]
        load_puzzle(new_active)

    save_book_config()
    return get_state()

@app.route('/api/book/clear-all', methods=['POST'])
def clear_all_puzzles():
    """
    Clears all uploaded puzzles in 1 click and resets the book to an empty/initial clean state.
    """
    # 1. Clean out all puzzle folders
    for p in list(BOOK.get("puzzles", [])):
        p_dir = os.path.join(BOOK_PUZZLES_DIR, p.get("dir_name", ""))
        if os.path.exists(p_dir):
            shutil.rmtree(p_dir, ignore_errors=True)

    if os.path.exists(BOOK_PUZZLES_DIR):
        for item in os.listdir(BOOK_PUZZLES_DIR):
            item_path = os.path.join(BOOK_PUZZLES_DIR, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)

    # 2. Reset config file
    if os.path.exists(BOOK_CONFIG_FILE):
        try:
            os.remove(BOOK_CONFIG_FILE)
        except Exception:
            pass

    # 3. Reset BOOK state and reinitialize
    BOOK["puzzles"] = []
    BOOK["active_id"] = 1
    init_book()
    save_book_config()
    return get_state()

@app.route('/api/book/update-config', methods=['POST'])
def update_book_config():
    data = request.json or {}
    if 'title' in data:
        BOOK["title"] = data['title']
    if 'page_size' in data:
        BOOK["page_size"] = data['page_size']
    if 'include_belongs_to' in data:
        BOOK["include_belongs_to"] = bool(data['include_belongs_to'])
    if 'include_instructions' in data:
        BOOK["include_instructions"] = bool(data['include_instructions'])
    if 'include_certificate' in data:
        BOOK["include_certificate"] = bool(data['include_certificate'])
    if 'solutions_per_page' in data:
        BOOK["solutions_per_page"] = int(data['solutions_per_page'])
    if 'target_differences' in data:
        BOOK["target_differences"] = max(1, min(20, int(data['target_differences'])))
    if 'only_completed_in_pdf' in data:
        BOOK["only_completed_in_pdf"] = bool(data['only_completed_in_pdf'])
    save_book_config()
    return get_state()

@app.route('/api/book/puzzle/<int:puzzle_id>/image/<img_type>', methods=['GET'])
def serve_puzzle_image(puzzle_id, img_type):
    p_info = next((p for p in BOOK["puzzles"] if p["id"] == puzzle_id), None)
    if not p_info:
        return jsonify({"error": "Puzzle not found"}), 404

    p_dir = os.path.join(BOOK_PUZZLES_DIR, p_info["dir_name"])
    if img_type == 'original':
        file_path = os.path.join(p_dir, 'original.png')
    elif img_type == 'modified':
        file_path = os.path.join(p_dir, 'modified.png')
    elif img_type == 'thumb':
        file_path = os.path.join(p_dir, 'thumb.png')
        if not os.path.exists(file_path):
            file_path = os.path.join(p_dir, 'modified.png')
    elif img_type == 'solution':
        mod_path = os.path.join(p_dir, 'modified.png')
        diff_path = os.path.join(p_dir, 'differences.json')
        if os.path.exists(mod_path):
            mod_bgr = cv2.imread(mod_path)
            diffs = []
            if os.path.exists(diff_path):
                with open(diff_path, 'r', encoding='utf-8') as df:
                    diffs = json.load(df)
            sol_bgr = engine.draw_solution_image(mod_bgr, diffs)
            sol_path = os.path.join(p_dir, 'solution.png')
            cv2.imwrite(sol_path, sol_bgr)
            return send_file(sol_path, mimetype='image/png')
        return jsonify({"error": "No image found"}), 404
    else:
        return jsonify({"error": "Invalid image type"}), 400

    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/png')
    return jsonify({"error": "File not found"}), 404

@app.route('/api/load-sample', methods=['POST'])
def load_sample():
    return add_sample_puzzle()

@app.route('/api/upload', methods=['POST'])
def upload_image():
    return upload_batch()

@app.route('/api/change-color', methods=['POST'])
def change_color():
    data = request.json or {}
    click_x = data.get('click_x')
    click_y = data.get('click_y')
    bbox = data.get('bbox')
    color_preset = data.get('preset', 'green')
    custom_shift = data.get('custom_hue_shift')
    tolerance = int(data.get('tolerance', 14))

    if STATE["current_bgr"] is None:
        return jsonify({"error": "No image loaded"}), 400

    new_img, diff_meta = engine.shift_color_precise(
        STATE["current_bgr"],
        click_x=click_x,
        click_y=click_y,
        bbox=bbox,
        target_color_preset=color_preset,
        custom_hue_shift=custom_shift,
        tolerance=tolerance
    )

    STATE["history"].append(STATE["current_bgr"].copy())
    STATE["current_bgr"] = new_img
    diff_meta["id"] = len(STATE["differences"]) + 1
    STATE["differences"].append(diff_meta)

    save_active_puzzle()
    return get_state()

@app.route('/api/erase', methods=['POST'])
def erase():
    data = request.json or {}
    mask_data_base64 = data.get('mask_base64')
    bbox = data.get('bbox')

    if STATE["current_bgr"] is None:
        return jsonify({"error": "No image loaded"}), 400

    img_h, img_w = STATE["current_bgr"].shape[:2]

    if mask_data_base64:
        header, encoded = mask_data_base64.split(',', 1) if ',' in mask_data_base64 else ('', mask_data_base64)
        mask_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(mask_bytes, np.uint8)
        mask_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        if mask_rgba.shape[2] == 4:
            mask_gray = mask_rgba[:, :, 3]
        else:
            mask_gray = cv2.cvtColor(mask_rgba, cv2.COLOR_BGR2GRAY)

        mask_gray = (mask_gray > 20).astype(np.uint8) * 255
        new_img, diff_meta = engine.erase_with_mask(STATE["current_bgr"], mask_gray)
    elif bbox:
        bx, by, bw, bh = [int(v) for v in bbox]
        mask_gray = np.zeros((img_h, img_w), dtype=np.uint8)
        cv2.rectangle(mask_gray, (bx, by), (bx + bw, by + bh), 255, -1)
        new_img, diff_meta = engine.erase_with_mask(STATE["current_bgr"], mask_gray)
    else:
        return jsonify({"error": "No mask or bbox provided"}), 400

    STATE["history"].append(STATE["current_bgr"].copy())
    STATE["current_bgr"] = new_img
    diff_meta["id"] = len(STATE["differences"]) + 1
    STATE["differences"].append(diff_meta)

    save_active_puzzle()
    return get_state()

@app.route('/api/flip', methods=['POST'])
def flip():
    data = request.json or {}
    bbox = data.get('bbox')
    if not bbox:
        return jsonify({"error": "No bbox provided"}), 400

    new_img, diff_meta = engine.flip_selection(STATE["current_bgr"], bbox)
    STATE["history"].append(STATE["current_bgr"].copy())
    STATE["current_bgr"] = new_img
    diff_meta["id"] = len(STATE["differences"]) + 1
    STATE["differences"].append(diff_meta)

    save_active_puzzle()
    return get_state()

@app.route('/api/clone', methods=['POST'])
def clone():
    data = request.json or {}
    src_bbox = data.get('src_bbox')
    dest_center = data.get('dest_center')
    blend_mode = data.get('blend_mode', 'seamless')

    if not src_bbox or not dest_center:
        return jsonify({"error": "Missing src_bbox or dest_center"}), 400

    if STATE["current_bgr"] is None:
        return jsonify({"error": "No image loaded"}), 400

    new_img, diff_meta = engine.clone_element(STATE["current_bgr"], src_bbox, dest_center, blend_mode=blend_mode)
    STATE["history"].append(STATE["current_bgr"].copy())
    STATE["current_bgr"] = new_img
    diff_meta["id"] = len(STATE["differences"]) + 1
    STATE["differences"].append(diff_meta)

    save_active_puzzle()
    return get_state()

@app.route('/api/undo', methods=['POST'])
def undo():
    if STATE["history"]:
        STATE["current_bgr"] = STATE["history"].pop()
        if STATE["differences"]:
            STATE["differences"].pop()
        save_active_puzzle()
    return get_state()

@app.route('/api/reset', methods=['POST'])
def reset():
    if STATE["original_bgr"] is not None:
        STATE["current_bgr"] = STATE["original_bgr"].copy()
        STATE["history"] = []
        STATE["differences"] = []
        save_active_puzzle()
    return get_state()

@app.route('/api/solution-image', methods=['GET'])
def get_solution():
    if STATE["current_bgr"] is None:
        return jsonify({"error": "No image loaded"}), 400
    sol = engine.draw_solution_image(STATE["current_bgr"], STATE["differences"])
    sol_path = os.path.join(OUTPUT_FOLDER, 'solution.png')
    cv2.imwrite(sol_path, sol)
    return send_file(sol_path, mimetype='image/png')

@app.route('/api/export-kdp-page', methods=['POST'])
def export_kdp_page():
    data = request.json or {}
    title = data.get('title', 'CAN YOU SPOT THE DIFFERENCES?')
    page_size = data.get('page_size', BOOK["page_size"])
    page_num = data.get('page_num', STATE["puzzle_id"])

    save_active_puzzle()
    page = engine.create_kdp_puzzle_page(
        STATE["original_bgr"],
        STATE["current_bgr"],
        num_diffs=len(STATE["differences"]),
        title=title,
        page_num=page_num,
        page_size=page_size
    )
    out_path = os.path.join(OUTPUT_FOLDER, f'kdp_puzzle_page_{page_num}.png')
    page.save(out_path, dpi=(300, 300))
    return send_file(out_path, mimetype='image/png', as_attachment=True, download_name=f'puzzle_page_{page_num}.png')

@app.route('/api/export-kdp-solution', methods=['POST'])
def export_kdp_solution():
    data = request.json or {}
    page_size = data.get('page_size', BOOK["page_size"])

    save_active_puzzle()
    sol_bgr = engine.draw_solution_image(STATE["current_bgr"], STATE["differences"])
    page = engine.create_kdp_solution_page(sol_bgr, STATE["differences"], page_size=page_size)
    out_path = os.path.join(OUTPUT_FOLDER, 'kdp_solution_page.png')
    page.save(out_path, dpi=(300, 300))
    return send_file(out_path, mimetype='image/png', as_attachment=True, download_name='solution_page.png')

@app.route('/api/export-book-pdf', methods=['POST'])
def export_book_pdf():
    data = request.json or {}
    title = data.get('title') or BOOK["title"]
    page_size = data.get('page_size') or BOOK["page_size"]
    include_belongs = data.get('include_belongs_to', BOOK["include_belongs_to"])
    include_instr = data.get('include_instructions', BOOK["include_instructions"])
    include_cert = data.get('include_certificate', BOOK["include_certificate"])
    sols_per_page = int(data.get('solutions_per_page', BOOK["solutions_per_page"]))
    only_completed = data.get('only_completed', BOOK.get("only_completed_in_pdf", True))
    target = BOOK.get("target_differences", 5)

    save_active_puzzle()

    puzzles_list = []
    for p in BOOK["puzzles"]:
        p_dir = os.path.join(BOOK_PUZZLES_DIR, p["dir_name"])
        orig_path = os.path.join(p_dir, 'original.png')
        mod_path = os.path.join(p_dir, 'modified.png')
        diff_path = os.path.join(p_dir, 'differences.json')

        if not os.path.exists(orig_path):
            continue

        orig_bgr = cv2.imread(orig_path)
        mod_bgr = cv2.imread(mod_path) if os.path.exists(mod_path) else orig_bgr.copy()

        diffs = []
        if os.path.exists(diff_path):
            try:
                with open(diff_path, 'r', encoding='utf-8') as df:
                    diffs = json.load(df)
            except Exception:
                diffs = []

        # If only_completed is requested, skip puzzles that haven't reached the target differences (or at least 1)
        if only_completed and len(diffs) < target:
            continue

        puzzles_list.append({
            "id": p["id"],
            "title": p.get("title", f"PUZZLE #{p['id']}"),
            "original_bgr": orig_bgr,
            "current_bgr": mod_bgr,
            "differences": diffs
        })

    # If only_completed was true but no puzzle reached target, fall back to any puzzle with diffs > 0
    if not puzzles_list and only_completed:
        for p in BOOK["puzzles"]:
            p_dir = os.path.join(BOOK_PUZZLES_DIR, p["dir_name"])
            orig_path = os.path.join(p_dir, 'original.png')
            mod_path = os.path.join(p_dir, 'modified.png')
            diff_path = os.path.join(p_dir, 'differences.json')
            if not os.path.exists(orig_path):
                continue
            orig_bgr = cv2.imread(orig_path)
            mod_bgr = cv2.imread(mod_path) if os.path.exists(mod_path) else orig_bgr.copy()
            diffs = []
            if os.path.exists(diff_path):
                try:
                    with open(diff_path, 'r', encoding='utf-8') as df:
                        diffs = json.load(df)
                except Exception:
                    diffs = []
            if len(diffs) > 0:
                puzzles_list.append({
                    "id": p["id"],
                    "title": p.get("title", f"PUZZLE #{p['id']}"),
                    "original_bgr": orig_bgr,
                    "current_bgr": mod_bgr,
                    "differences": diffs
                })

    if not puzzles_list:
        return jsonify({"error": "No modified puzzles found in the book. Please add differences to at least one puzzle before exporting PDF!"}), 400

    pdf_filename = 'Spot_The_Differences_Book_300DPI.pdf'
    pdf_out_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

    engine.compile_full_kdp_book(
        puzzles_list,
        pdf_out_path,
        title=title,
        page_size=page_size,
        include_belongs_to=include_belongs,
        include_instructions=include_instr,
        include_certificate=include_cert,
        solutions_per_page=sols_per_page
    )

    return send_file(pdf_out_path, mimetype='application/pdf', as_attachment=True, download_name=pdf_filename)

# ---------------------------------------------------------------------------
# AI PROMPT STUDIO ENDPOINTS (Winter/Christmas & KDP Niches)
# ---------------------------------------------------------------------------

@app.route('/api/prompts/niches', methods=['GET'])
def get_niches():
    return jsonify(prompt_engine.get_available_niches())

@app.route('/api/prompts/generate', methods=['POST'])
def generate_prompts_endpoint():
    data = request.json or {}
    niche = data.get('niche', 'winter_christmas')
    count = int(data.get('count', 50))
    target_model = data.get('target_model', 'midjourney')
    aspect_ratio = data.get('aspect_ratio', '1:1')

    prompts = prompt_engine.generate_prompts(
        niche=niche,
        count=min(max(1, count), 200),
        target_model=target_model,
        aspect_ratio=aspect_ratio
    )
    return jsonify({
        "niche": niche,
        "count": len(prompts),
        "target_model": target_model,
        "aspect_ratio": aspect_ratio,
        "prompts": prompts
    })

@app.route('/api/prompts/export', methods=['POST'])
def export_prompts_file():
    import io
    import csv
    data = request.json or {}
    export_format = data.get('format', 'txt')
    prompts = data.get('prompts', [])

    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Title', 'Prompt', 'Suggested Differences', 'Target Model'])
        for p in prompts:
            diffs_str = " | ".join(p.get('suggested_differences', []))
            writer.writerow([p.get('id'), p.get('title'), p.get('prompt'), diffs_str, p.get('target_model')])
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='kdp_prompts_batch.csv')
    else:
        content = []
        content.append("="*70)
        content.append("  SPOT THE DIFFERENCE STUDIO - KDP AI IMAGE PROMPT BATCH")
        content.append(f"  Total Prompts: {len(prompts)}  |  Niche: Winter & Christmas For Kids")
        content.append("="*70 + "\n")
        for p in prompts:
            content.append(f"[PROMPT #{p.get('id')}] - {p.get('title')}")
            content.append("-" * 50)
            content.append(p.get('prompt'))
            content.append("\nSuggested Differences to Create in Studio:")
            for d in p.get('suggested_differences', []):
                content.append(f"  * {d}")
            content.append("\n" + "="*70 + "\n")
        text_data = "\n".join(content)
        mem = io.BytesIO(text_data.encode('utf-8'))
        return send_file(mem, mimetype='text/plain', as_attachment=True, download_name='kdp_winter_prompts_50.txt')

if __name__ == '__main__':
    print("Starting Spot the Difference Studio at http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=False)
