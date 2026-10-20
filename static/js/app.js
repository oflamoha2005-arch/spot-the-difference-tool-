// Spot The Difference Studio - Client Logic
document.addEventListener('DOMContentLoaded', () => {
  // UI Elements
  const baseImage = document.getElementById('baseImage');
  const interactiveCanvas = document.getElementById('interactiveCanvas');
  const ctx = interactiveCanvas.getContext('2d');

  const splitImgOriginal = document.getElementById('splitImgOriginal');
  const splitImgModified = document.getElementById('splitImgModified');
  const solutionImg = document.getElementById('solutionImg');

  const diffCountBadge = document.getElementById('diffCountBadge');
  const diffTotal = document.getElementById('diffTotal');
  const diffList = document.getElementById('diffList');
  const statusIndicator = document.getElementById('statusIndicator');

  // Tool Elements
  const toolButtons = document.querySelectorAll('.tool-card');
  const colorOptions = document.getElementById('colorOptions');
  const eraseOptions = document.getElementById('eraseOptions');
  const flipOptions = document.getElementById('flipOptions');
  const cloneOptions = document.getElementById('cloneOptions');
  const cloneStep1 = document.getElementById('cloneStep1');
  const cloneStep2 = document.getElementById('cloneStep2');
  const btnCancelClone = document.getElementById('btnCancelClone');
  const cloneBlendMode = document.getElementById('cloneBlendMode');

  const colorSwatches = document.querySelectorAll('.color-swatch');
  const toleranceSlider = document.getElementById('toleranceSlider');
  const toleranceVal = document.getElementById('toleranceVal');

  const brushSizeSlider = document.getElementById('brushSizeSlider');
  const brushSizeVal = document.getElementById('brushSizeVal');
  const btnApplyErase = document.getElementById('btnApplyErase');
  const btnClearBrush = document.getElementById('btnClearBrush');

  // Top Nav Actions
  const btnLoadSample = document.getElementById('btnLoadSample');
  const fileUploadInput = document.getElementById('fileUploadInput');
  const btnUndo = document.getElementById('btnUndo');
  const btnReset = document.getElementById('btnReset');
  const btnUndoLastDiff = document.getElementById('btnUndoLastDiff');

  // Zoom & Pan Elements
  const canvasViewport = document.getElementById('canvasViewport');
  const canvasWrapper = document.querySelector('.canvas-wrapper');
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnZoomReset = document.getElementById('btnZoomReset');
  const btnPanToggle = document.getElementById('btnPanToggle');
  const zoomLevelDisplay = document.getElementById('zoomLevelDisplay');

  // View Tabs
  const tabButtons = document.querySelectorAll('.tab-btn');
  const viewPanels = document.querySelectorAll('.view-panel');

  // Export Actions
  const btnExportPuzzlePng = document.getElementById('btnExportPuzzlePng');
  const btnExportSolutionPng = document.getElementById('btnExportSolutionPng');
  const btnExportFullPdf = document.getElementById('btnExportFullPdf');
  const kdpPageSize = document.getElementById('kdpPageSize');
  const kdpTitle = document.getElementById('kdpTitle');
  const kdpPageNum = document.getElementById('kdpPageNum');

  // State
  let currentTool = 'color'; // 'color', 'erase', 'flip', 'clone'
  let selectedColor = 'green';
  let tolerance = 22;
  let brushSize = 28;

  let cloneState = 'select_source'; // 'select_source' | 'paste_target'
  let cloneSourceBox = null;
  let clonePreviewPos = null;

  let currentZoom = 1.0;
  let panX = 0, panY = 0;
  let isPanMode = false;
  let isSpacePressed = false;
  let isPanningDrag = false;
  let panMouseStartX = 0, panMouseStartY = 0;

  let isInteracting = false;
  let startX = 0, startY = 0;
  let currentBox = null;
  let maskCanvas = document.createElement('canvas');
  let maskCtx = maskCanvas.getContext('2d');
  let hasBrushStroke = false;

  // Initialize Canvas Dimensions
  function syncCanvasSize() {
    if (!baseImage.complete || baseImage.naturalWidth === 0) return;
    interactiveCanvas.width = baseImage.naturalWidth;
    interactiveCanvas.height = baseImage.naturalHeight;
    maskCanvas.width = baseImage.naturalWidth;
    maskCanvas.height = baseImage.naturalHeight;
    redrawCanvas();
  }

  baseImage.onload = syncCanvasSize;
  window.addEventListener('resize', syncCanvasSize);

  // Status Helper
  function setStatus(text, isBusy = false) {
    statusIndicator.textContent = text;
    statusIndicator.style.color = isBusy ? 'var(--accent-amber)' : 'var(--accent-emerald)';
    statusIndicator.style.borderColor = isBusy ? 'rgba(245, 158, 11, 0.4)' : 'rgba(16, 185, 129, 0.3)';
    statusIndicator.style.background = isBusy ? 'rgba(245, 158, 11, 0.1)' : 'rgba(16, 185, 129, 0.1)';
  }

  // Redraw Canvas Overlay
  function redrawCanvas() {
    ctx.clearRect(0, 0, interactiveCanvas.width, interactiveCanvas.height);

    if (currentTool === 'erase' && hasBrushStroke) {
      // Draw mask overlay with vibrant semi-transparent orange
      ctx.drawImage(maskCanvas, 0, 0);
    } else if (currentTool === 'flip' && currentBox) {
      ctx.strokeStyle = '#06B6D4';
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 6]);
      ctx.strokeRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
      ctx.fillStyle = 'rgba(6, 182, 212, 0.15)';
      ctx.fillRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
    } else if (currentTool === 'clone') {
      if (cloneState === 'select_source' && currentBox) {
        ctx.strokeStyle = '#10B981';
        ctx.lineWidth = 3;
        ctx.setLineDash([6, 6]);
        ctx.strokeRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
        ctx.fillRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
      } else if (cloneState === 'paste_target' && cloneSourceBox) {
        // Draw dashed outline at original source position
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.7)';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(cloneSourceBox.x, cloneSourceBox.y, cloneSourceBox.w, cloneSourceBox.h);

        // Draw preview of clone target centered at hover point
        if (clonePreviewPos) {
          const px = clonePreviewPos.x - cloneSourceBox.w / 2;
          const py = clonePreviewPos.y - cloneSourceBox.h / 2;
          ctx.strokeStyle = '#06B6D4';
          ctx.lineWidth = 3;
          ctx.setLineDash([6, 6]);
          ctx.strokeRect(px, py, cloneSourceBox.w, cloneSourceBox.h);
          ctx.fillStyle = 'rgba(6, 182, 212, 0.2)';
          ctx.fillRect(px, py, cloneSourceBox.w, cloneSourceBox.h);

          // Center indicator
          ctx.beginPath();
          ctx.arc(clonePreviewPos.x, clonePreviewPos.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#06B6D4';
          ctx.fill();
        }
      }
    }
  }

  // Coordinate Conversion: Screen to Original Image Pixels
  function getImgCoords(e) {
    const rect = interactiveCanvas.getBoundingClientRect();
    const scaleX = interactiveCanvas.width / rect.width;
    const scaleY = interactiveCanvas.height / rect.height;
    return {
      x: Math.round((e.clientX - rect.left) * scaleX),
      y: Math.round((e.clientY - rect.top) * scaleY)
    };
  }

  // Tool Switching
  toolButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      toolButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTool = btn.dataset.tool;

      colorOptions.classList.add('hidden');
      eraseOptions.classList.add('hidden');
      flipOptions.classList.add('hidden');
      if (cloneOptions) cloneOptions.classList.add('hidden');

      if (currentTool === 'color') colorOptions.classList.remove('hidden');
      if (currentTool === 'erase') eraseOptions.classList.remove('hidden');
      if (currentTool === 'flip') flipOptions.classList.remove('hidden');
      if (currentTool === 'clone') {
        cloneOptions.classList.remove('hidden');
        resetCloneTool();
      }

      clearSelection();
    });
  });

  // Color Swatches
  colorSwatches.forEach(sw => {
    sw.addEventListener('click', () => {
      colorSwatches.forEach(s => s.classList.remove('active'));
      sw.classList.add('active');
      selectedColor = sw.dataset.color;
    });
  });

  // Tolerance Slider
  toleranceSlider.addEventListener('input', (e) => {
    tolerance = parseInt(e.target.value);
    toleranceVal.textContent = tolerance;
  });

  // Brush Size Slider
  brushSizeSlider.addEventListener('input', (e) => {
    brushSize = parseInt(e.target.value);
    brushSizeVal.textContent = `${brushSize}px`;
  });

  // Clear Brush/Selection
  function clearSelection() {
    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
    hasBrushStroke = false;
    currentBox = null;
    redrawCanvas();
  }

  btnClearBrush.addEventListener('click', clearSelection);

  // Tab View Switcher
  tabButtons.forEach(tab => {
    tab.addEventListener('click', () => {
      tabButtons.forEach(t => t.classList.remove('active'));
      viewPanels.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const viewId = `${tab.dataset.view}View`;
      const targetPanel = document.getElementById(viewId);
      if (targetPanel) targetPanel.classList.add('active');

      if (tab.dataset.view === 'solution') {
        solutionImg.src = `/api/solution-image?t=${Date.now()}`;
      }
    });
  });

  // Canvas Mouse Interactions
  interactiveCanvas.addEventListener('mousedown', (e) => {
    if (isPanMode || isSpacePressed || e.button === 1) return; // Ignore when panning

    isInteracting = true;
    const pt = getImgCoords(e);
    startX = pt.x;
    startY = pt.y;

    if (currentTool === 'erase') {
      hasBrushStroke = true;
      maskCtx.fillStyle = 'rgba(244, 63, 94, 0.65)';
      maskCtx.strokeStyle = 'rgba(244, 63, 94, 0.65)';
      maskCtx.lineWidth = brushSize;
      maskCtx.lineCap = 'round';
      maskCtx.lineJoin = 'round';
      maskCtx.beginPath();
      maskCtx.arc(pt.x, pt.y, brushSize / 2, 0, Math.PI * 2);
      maskCtx.fill();
      redrawCanvas();
    }
  });

  interactiveCanvas.addEventListener('mousemove', (e) => {
    const pt = getImgCoords(e);

    if (currentTool === 'clone' && cloneState === 'paste_target') {
      clonePreviewPos = pt;
      redrawCanvas();
      return;
    }

    if (isInteracting && !isPanMode && !isSpacePressed) {
      if (currentTool === 'erase') {
        maskCtx.beginPath();
        maskCtx.moveTo(startX, startY);
        maskCtx.lineTo(pt.x, pt.y);
        maskCtx.stroke();
        startX = pt.x;
        startY = pt.y;
        redrawCanvas();
      } else if (currentTool === 'flip' || (currentTool === 'clone' && cloneState === 'select_source')) {
        currentBox = {
          x: Math.min(startX, pt.x),
          y: Math.min(startY, pt.y),
          w: Math.abs(pt.x - startX),
          h: Math.abs(pt.y - startY)
        };
        redrawCanvas();
      }
    }
  });

  interactiveCanvas.addEventListener('mouseup', async (e) => {
    if (isPanMode || isSpacePressed) return;
    const pt = getImgCoords(e);

    if (currentTool === 'clone' && cloneState === 'paste_target') {
      if (cloneSourceBox) {
        await applyClone(cloneSourceBox, pt.x, pt.y);
      }
      return;
    }

    if (!isInteracting) return;
    isInteracting = false;

    if (currentTool === 'color') {
      // Color swap triggered on click!
      await applyColorSwap(pt.x, pt.y);
    } else if (currentTool === 'flip' && currentBox && currentBox.w > 10 && currentBox.h > 10) {
      await applyFlip(currentBox);
    } else if (currentTool === 'clone' && cloneState === 'select_source' && currentBox && currentBox.w > 10 && currentBox.h > 10) {
      cloneSourceBox = { ...currentBox };
      cloneState = 'paste_target';
      currentBox = null;
      if (cloneStep1) cloneStep1.classList.add('hidden');
      if (cloneStep2) cloneStep2.classList.remove('hidden');
      setStatus('العنصر محدد! كليكي دابا فالمكان اللي باغي تلصقو فيه');
      redrawCanvas();
    }
  });

  function resetCloneTool() {
    cloneState = 'select_source';
    cloneSourceBox = null;
    clonePreviewPos = null;
    currentBox = null;
    if (cloneStep1) cloneStep1.classList.remove('hidden');
    if (cloneStep2) cloneStep2.classList.add('hidden');
    redrawCanvas();
  }

  if (btnCancelClone) {
    btnCancelClone.addEventListener('click', resetCloneTool);
  }

  // Clone Action
  async function applyClone(srcBox, destX, destY) {
    setStatus('Cloning and blending item...', true);
    try {
      const res = await fetch('/api/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          src_bbox: [srcBox.x, srcBox.y, srcBox.w, srcBox.h],
          dest_center: [destX, destY],
          blend_mode: cloneBlendMode ? cloneBlendMode.value : 'seamless'
        })
      });
      const data = await res.json();
      resetCloneTool();
      updateStateUI(data);
      setStatus('Item duplicated successfully!');
    } catch (err) {
      console.error(err);
      setStatus('Error duplicating item', false);
    }
  }

  // Color Swap Action
  async function applyColorSwap(clickX, clickY) {
    setStatus('Changing color...', true);
    try {
      const res = await fetch('/api/change-color', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          click_x: clickX,
          click_y: clickY,
          preset: selectedColor,
          tolerance: tolerance
        })
      });
      const data = await res.json();
      updateStateUI(data);
      setStatus('Color changed successfully!');
    } catch (err) {
      console.error(err);
      setStatus('Error modifying color', false);
    }
  }

  // Erase Action
  btnApplyErase.addEventListener('click', async () => {
    if (!hasBrushStroke) {
      alert('Please paint over the object you want to erase first!');
      return;
    }

    setStatus('Erasing object with background healing...', true);
    const maskBase64 = maskCanvas.toDataURL('image/png');

    try {
      const res = await fetch('/api/erase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mask_base64: maskBase64 })
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Object erased cleanly!');
    } catch (err) {
      console.error(err);
      setStatus('Error erasing object', false);
    }
  });

  // Flip Action
  async function applyFlip(box) {
    setStatus('Flipping element...', true);
    try {
      const res = await fetch('/api/flip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bbox: [box.x, box.y, box.w, box.h] })
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Element flipped!');
    } catch (err) {
      console.error(err);
      setStatus('Error flipping element', false);
    }
  }

  // Update State UI
  function updateStateUI(state) {
    diffCountBadge.textContent = state.differences_count;
    diffTotal.textContent = state.differences_count;
    btnUndo.disabled = !state.has_undo;
    if (btnUndoLastDiff) btnUndoLastDiff.disabled = !state.has_undo;

    // Refresh images
    const t = Date.now();
    baseImage.src = `${state.modified_url}&t=${t}`;
    splitImgOriginal.src = `${state.image_url}?t=${t}`;
    splitImgModified.src = `${state.modified_url}&t=${t}`;
    solutionImg.src = `/api/solution-image?t=${t}`;

    // Render differences list
    if (state.differences.length === 0) {
      diffList.innerHTML = `
        <div class="empty-diff-state">
          <span>🎯</span>
          <p>No differences yet. Click or brush on the image to create your first difference!</p>
        </div>
      `;
    } else {
      diffList.innerHTML = state.differences.map((d, i) => `
        <div class="diff-item">
          <div>
            <span class="diff-badge">${i + 1}</span>
            <strong>${d.label}</strong>
          </div>
          <span style="color:var(--text-dim);font-size:0.7rem;">(${d.center[0]}, ${d.center[1]})</span>
        </div>
      `).join('');
    }
  }

  // Load Initial State
  async function fetchState() {
    try {
      const res = await fetch('/api/state');
      const data = await res.json();
      updateStateUI(data);
    } catch (err) {
      console.error(err);
    }
  }
  fetchState();

  // Undo Action
  async function triggerUndo() {
    setStatus('Undoing last modification...', true);
    try {
      const res = await fetch('/api/undo', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Last modification undone.');
    } catch (err) {
      console.error(err);
      setStatus('Error undoing modification', false);
    }
  }

  btnUndo.addEventListener('click', triggerUndo);
  if (btnUndoLastDiff) {
    btnUndoLastDiff.addEventListener('click', triggerUndo);
  }

  // Reset
  btnReset.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to reset all differences?')) return;
    setStatus('Resetting...', true);
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Reset to original.');
    } catch (err) {
      console.error(err);
    }
  });

  // Load Sample
  btnLoadSample.addEventListener('click', async () => {
    setStatus('Loading sample...', true);
    try {
      const res = await fetch('/api/load-sample', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Sample park image loaded.');
    } catch (err) {
      console.error(err);
    }
  });

  // Upload Custom Image
  fileUploadInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setStatus('Uploading image...', true);
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Custom image uploaded!');
    } catch (err) {
      console.error(err);
      setStatus('Upload failed', false);
    }
  });

  // KDP Exports
  btnExportPuzzlePng.addEventListener('click', async () => {
    setStatus('Generating 300 DPI Puzzle Page PNG...', true);
    try {
      const res = await fetch('/api/export-kdp-page', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: kdpTitle.value,
          page_size: kdpPageSize.value,
          page_num: kdpPageNum.value
        })
      });
      const blob = await res.blob();
      downloadBlob(blob, `KDP_Puzzle_Page_${kdpPageNum.value}_300DPI.png`);
      setStatus('Puzzle Page PNG downloaded!');
    } catch (err) {
      console.error(err);
      setStatus('Export error', false);
    }
  });

  btnExportSolutionPng.addEventListener('click', async () => {
    setStatus('Generating 300 DPI Solution Page PNG...', true);
    try {
      const res = await fetch('/api/export-kdp-solution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page_size: kdpPageSize.value
        })
      });
      const blob = await res.blob();
      downloadBlob(blob, 'KDP_Solution_Page_300DPI.png');
      setStatus('Solution Page PNG downloaded!');
    } catch (err) {
      console.error(err);
      setStatus('Export error', false);
    }
  });

  btnExportFullPdf.addEventListener('click', async () => {
    setStatus('Generating complete Print-Ready Book PDF (300 DPI)...', true);
    try {
      const res = await fetch('/api/export-book-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: kdpTitle.value,
          page_size: kdpPageSize.value
        })
      });
      const blob = await res.blob();
      downloadBlob(blob, 'Spot_The_Differences_Book_300DPI.pdf');
      setStatus('Complete PDF Book downloaded!');
    } catch (err) {
      console.error(err);
      setStatus('Export error', false);
    }
  });

  function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  // --- Zoom & Pan Engine ---
  function updateTransform() {
    if (!canvasWrapper) return;
    canvasWrapper.style.transform = `scale(${currentZoom}) translate(${panX}px, ${panY}px)`;
    if (zoomLevelDisplay) {
      zoomLevelDisplay.textContent = `${Math.round(currentZoom * 100)}%`;
    }
  }

  function setZoom(val) {
    currentZoom = Math.min(3.5, Math.max(0.5, Math.round(val * 100) / 100));
    if (currentZoom === 1.0) {
      panX = 0;
      panY = 0;
    }
    updateTransform();
  }

  if (btnZoomIn) btnZoomIn.addEventListener('click', () => setZoom(currentZoom + 0.25));
  if (btnZoomOut) btnZoomOut.addEventListener('click', () => setZoom(currentZoom - 0.25));
  if (btnZoomReset) btnZoomReset.addEventListener('click', () => setZoom(1.0));

  if (btnPanToggle) {
    btnPanToggle.addEventListener('click', () => {
      isPanMode = !isPanMode;
      btnPanToggle.classList.toggle('active', isPanMode);
      canvasViewport.classList.toggle('pan-active', isPanMode);
      if (isPanMode) {
        setStatus('وضع التحريك شغال: جر الماوس لتحريك الصورة');
      } else {
        setStatus('Ready');
      }
    });
  }

  // Quick Pan with Spacebar
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target === document.body && !isSpacePressed) {
      isSpacePressed = true;
      canvasViewport.classList.add('pan-active');
    }
  });

  window.addEventListener('keyup', (e) => {
    if (e.code === 'Space') {
      isSpacePressed = false;
      if (!isPanMode) {
        canvasViewport.classList.remove('pan-active');
      }
    }
  });

  // Mouse wheel zoom
  if (canvasViewport) {
    canvasViewport.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      setZoom(currentZoom + delta);
    }, { passive: false });

    // Drag to pan
    canvasViewport.addEventListener('mousedown', (e) => {
      if (isPanMode || isSpacePressed || e.button === 1) {
        isPanningDrag = true;
        panMouseStartX = e.clientX - panX * currentZoom;
        panMouseStartY = e.clientY - panY * currentZoom;
        canvasViewport.classList.add('pan-grabbing');
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (isPanningDrag) {
        panX = (e.clientX - panMouseStartX) / currentZoom;
        panY = (e.clientY - panMouseStartY) / currentZoom;
        updateTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      if (isPanningDrag) {
        isPanningDrag = false;
        canvasViewport.classList.remove('pan-grabbing');
      }
    });
  }
});
