import os
import cv2
import json
import base64
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import engine

app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Application In-Memory State
STATE = {
    "original_bgr": None,
    "current_bgr": None,
    "history": [],
    "differences": [],
    "image_name": "sample_park.jpg",
    "image_url": "/static/samples/sample_park.jpg",
    "modified_url": "/static/samples/sample_park.jpg"
}

def load_initial_image():
    sample_path = os.path.join(os.path.dirname(__file__), 'static', 'samples', 'sample_park.jpg')
    if os.path.exists(sample_path):
        bgr = cv2.imread(sample_path)
        STATE["original_bgr"] = bgr.copy()
        STATE["current_bgr"] = bgr.copy()
        STATE["history"] = []
        STATE["differences"] = []
        cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), bgr)
        STATE["modified_url"] = '/outputs/current_modified.png'
        STATE["image_url"] = '/static/samples/sample_park.jpg'

load_initial_image()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify({
        "image_url": STATE["image_url"],
        "modified_url": STATE["modified_url"] + f"?t={os.urandom(4).hex()}",
        "differences_count": len(STATE["differences"]),
        "differences": STATE["differences"],
        "has_undo": len(STATE["history"]) > 0
    })

@app.route('/api/load-sample', methods=['POST'])
def load_sample():
    load_initial_image()
    return get_state()

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # Read image
    bgr = cv2.imread(save_path)
    if bgr is None:
        return jsonify({"error": "Invalid image file"}), 400

    STATE["original_bgr"] = bgr.copy()
    STATE["current_bgr"] = bgr.copy()
    STATE["history"] = []
    STATE["differences"] = []
    STATE["image_name"] = filename
    STATE["image_url"] = f'/static/uploads/{filename}'

    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), bgr)
    STATE["modified_url"] = '/outputs/current_modified.png'

    return get_state()

@app.route('/api/change-color', methods=['POST'])
def change_color():
    data = request.json or {}
    click_x = data.get('click_x')
    click_y = data.get('click_y')
    bbox = data.get('bbox')
    color_preset = data.get('preset', 'green')
    custom_shift = data.get('custom_hue_shift')
    tolerance = int(data.get('tolerance', 22))

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

    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), new_img)
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
        # Decode base64 mask
        header, encoded = mask_data_base64.split(',', 1) if ',' in mask_data_base64 else ('', mask_data_base64)
        mask_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(mask_bytes, np.uint8)
        mask_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        # Extract alpha or grayscale
        if mask_rgba.shape[2] == 4:
            mask_gray = mask_rgba[:, :, 3]
        else:
            mask_gray = cv2.cvtColor(mask_rgba, cv2.COLOR_BGR2GRAY)
            
        mask_gray = (mask_gray > 20).astype(np.uint8) * 255
        new_img, diff_meta = engine.erase_with_mask(STATE["current_bgr"], mask_gray)
    elif bbox:
        # Erase via bounding box
        bx, by, bw, bh = [int(v) for v in bbox]
        mask_gray = np.zeros((img_h, img_w), dtype=np.uint8)
        cv2.ellipse(mask_gray, (bx + bw//2, by + bh//2), (bw//2, bh//2), 0, 0, 360, 255, -1)
        new_img, diff_meta = engine.erase_with_mask(STATE["current_bgr"], mask_gray)
    else:
        return jsonify({"error": "No mask or bbox provided"}), 400

    STATE["history"].append(STATE["current_bgr"].copy())
    STATE["current_bgr"] = new_img
    diff_meta["id"] = len(STATE["differences"]) + 1
    STATE["differences"].append(diff_meta)

    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), new_img)
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

    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), new_img)
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

    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), new_img)
    return get_state()

@app.route('/api/undo', methods=['POST'])
def undo():
    if STATE["history"]:
        STATE["current_bgr"] = STATE["history"].pop()
        if STATE["differences"]:
            STATE["differences"].pop()
        cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), STATE["current_bgr"])
    return get_state()

@app.route('/api/reset', methods=['POST'])
def reset():
    if STATE["original_bgr"] is not None:
        STATE["current_bgr"] = STATE["original_bgr"].copy()
        STATE["history"] = []
        STATE["differences"] = []
        cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'current_modified.png'), STATE["current_bgr"])
    return get_state()

@app.route('/api/solution-image', methods=['GET'])
def get_solution():
    if STATE["original_bgr"] is None:
        return jsonify({"error": "No image loaded"}), 400
    sol = engine.draw_solution_image(STATE["current_bgr"], STATE["differences"])
    sol_path = os.path.join(OUTPUT_FOLDER, 'solution.png')
    cv2.imwrite(sol_path, sol)
    return send_file(sol_path, mimetype='image/png')

@app.route('/api/export-kdp-page', methods=['POST'])
def export_kdp_page():
    data = request.json or {}
    title = data.get('title', 'CAN YOU SPOT THE DIFFERENCES?')
    page_size = data.get('page_size', '8.5x8.5')
    page_num = data.get('page_num', 1)

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
    page_size = data.get('page_size', '8.5x8.5')
    
    sol_bgr = engine.draw_solution_image(STATE["current_bgr"], STATE["differences"])
    page = engine.create_kdp_solution_page(sol_bgr, STATE["differences"], page_size=page_size)
    out_path = os.path.join(OUTPUT_FOLDER, 'kdp_solution_page.png')
    page.save(out_path, dpi=(300, 300))
    return send_file(out_path, mimetype='image/png', as_attachment=True, download_name='solution_page.png')

@app.route('/api/export-book-pdf', methods=['POST'])
def export_book_pdf():
    data = request.json or {}
    title = data.get('title', 'CAN YOU SPOT THE DIFFERENCES?')
    page_size = data.get('page_size', '8.5x8.5')

    # Generate Puzzle Page
    puzzle_page = engine.create_kdp_puzzle_page(
        STATE["original_bgr"],
        STATE["current_bgr"],
        num_diffs=len(STATE["differences"]),
        title=title,
        page_num=1,
        page_size=page_size
    )

    # Generate Solution Page
    sol_bgr = engine.draw_solution_image(STATE["current_bgr"], STATE["differences"])
    sol_page = engine.create_kdp_solution_page(sol_bgr, STATE["differences"], page_size=page_size)

    # Combine into PDF
    pdf_path = os.path.join(OUTPUT_FOLDER, 'Spot_The_Differences_Book_300DPI.pdf')
    puzzle_page.save(pdf_path, "PDF", resolution=300.0, save_all=True, append_images=[sol_page])

    return send_file(pdf_path, mimetype='application/pdf', as_attachment=True, download_name='Spot_The_Differences_Book_300DPI.pdf')

if __name__ == '__main__':
    print("Starting Spot the Difference Studio at http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=False)
