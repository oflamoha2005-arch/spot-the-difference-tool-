# 🔍 Spot The Difference Studio - KDP Book Creator

> **Professional 300 DPI Amazon KDP Activity Book Engine & Image Puzzle Creator**  
> Create, modify, and publish print-ready "Spot The Difference" activity books with zero external APIs, 100% offline and lightning-fast.

---

## ✨ Features

- **🎨 Smart Color Swap:**
  - Tight HSV color isolation with flood-fill contour protection.
  - Changes target elements without affecting surrounding background or foliage.
  - Multi-color presets (Green, Yellow, Blue, Purple, Orange, Red) preserving natural lighting and shadows.

- **🧽 Smart Background Eraser:**
  - Inpaints unwanted objects seamlessly with OpenCV Telea algorithm.
  - Automatic mask dilation to prevent ghost edges or color fringes.

- **🔄 Flip Tool:**
  - Flips selected objects horizontally (e.g., animals, birds, vehicles).

- **📋 Clone / Duplicate Tool:**
  - Duplicate any element (apple, bird, star) and paste it anywhere on the canvas.
  - Uses OpenCV `seamlessClone` for natural lighting integration.

- **🔍 Interactive Zoom & Pan:**
  - Smooth zoom from 50% up to 350% magnification.
  - Spacebar / Pan mode dragging to inspect and edit microscopic details.
  - Mouse wheel zoom support.

- **🎯 Automated Solution Key:**
  - Real-time solution generation with numbered high-visibility coral badges.
  - List of differences with exact coordinates and labels.

- **📕 Amazon KDP Print-Ready 300 DPI Export:**
  - Pre-calibrated trim sizes: **8.5" x 8.5" (Square)** & **8.5" x 11" (Portrait)**.
  - Safe margins, headers, subtitles, and interactive checklist circles for kids.
  - Export single puzzle page (PNG 300 DPI), solution page (PNG 300 DPI), or complete multi-page book (PDF 300 DPI).

---

## 🚀 Quick Start (Windows)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/oflamoha2005-arch/spot-the-difference-tool-.git
   cd spot-the-difference-tool-
   ```

2. **Run directly:**
   - Double-click **`RUN_STUDIO.lnk`** or **`run.bat`**.
   - Your browser will open automatically at `http://127.0.0.1:5000`.

---

## 🛠️ Manual Installation (Any OS)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 📁 Project Structure

```
spot-the-difference-tool-/
│
├── app.py                 # Flask server & REST API
├── engine.py              # OpenCV & PIL image processing core
├── run.bat                # Windows launcher script
├── START_STUDIO.bat       # Alternative batch launcher
├── requirements.txt       # Python dependencies
│
├── static/
│   ├── css/style.css      # Dark glassmorphism UI styling
│   ├── js/app.js          # Interactive canvas & client logic
│   ├── samples/           # High-resolution sample park image
│   └── uploads/           # User-uploaded images
│
├── templates/
│   └── index.html         # Web application UI
│
└── outputs/               # Generated KDP PNG pages & 300 DPI PDFs
```

---

## 📄 License

MIT License. Free to use for commercial Amazon KDP activity book publishing.
