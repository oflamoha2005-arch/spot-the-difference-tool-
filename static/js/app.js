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
  const btnEraseModeBrush = document.getElementById('btnEraseModeBrush');
  const btnEraseModeBox = document.getElementById('btnEraseModeBox');
  const eraseBrushControls = document.getElementById('eraseBrushControls');
  const sizePresetBtns = document.querySelectorAll('.size-preset-btn');
  const eraseAutoApplyToggle = document.getElementById('eraseAutoApplyToggle');
  const eraseTipCard = document.getElementById('eraseTipCard');

  const btnColorModeClick = document.getElementById('btnColorModeClick');
  const btnColorModeBox = document.getElementById('btnColorModeBox');
  const colorTipCard = document.getElementById('colorTipCard');

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
  let selectedColor = 'purple';
  let tolerance = 14;
  let colorMode = 'click'; // 'click' or 'box'
  let clickIndicator = null;
  let clickIndicatorTimer = null;
  let brushSize = 35;
  let eraseMode = 'brush'; // 'brush' or 'box'
  let eraseAutoApply = true;
  let brushCursorPos = null;

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
    if (interactiveCanvas.width === baseImage.naturalWidth && interactiveCanvas.height === baseImage.naturalHeight) {
      return; // Dimensions unchanged: avoid wiping canvas buffer
    }
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

    if (currentTool === 'erase') {
      if (eraseMode === 'brush') {
        if (hasBrushStroke) {
          ctx.drawImage(maskCanvas, 0, 0);
        }
        // Draw live circular brush cursor
        if (brushCursorPos && !isPanMode && !isSpacePressed) {
          ctx.beginPath();
          ctx.arc(brushCursorPos.x, brushCursorPos.y, brushSize / 2, 0, Math.PI * 2);
          ctx.strokeStyle = '#F43F5E';
          ctx.lineWidth = Math.max(1.5, 2.5 / currentZoom);
          ctx.setLineDash([4, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      } else if (eraseMode === 'box' && currentBox) {
        ctx.strokeStyle = '#F43F5E';
        ctx.lineWidth = 3;
        ctx.setLineDash([6, 6]);
        ctx.strokeRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
        ctx.fillStyle = 'rgba(244, 63, 94, 0.2)';
        ctx.fillRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
        ctx.setLineDash([]);
      }
    } else if (currentTool === 'color' && colorMode === 'box' && currentBox) {
      ctx.strokeStyle = '#8B5CF6';
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 6]);
      ctx.strokeRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
      ctx.fillStyle = 'rgba(139, 92, 246, 0.2)';
      ctx.fillRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
      ctx.setLineDash([]);
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

    // Draw animated click ripple indicator if active
    if (clickIndicator) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(clickIndicator.x, clickIndicator.y, clickIndicator.radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(139, 92, 246, ${clickIndicator.opacity})`;
      ctx.lineWidth = Math.max(2, 3 / currentZoom);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(clickIndicator.x, clickIndicator.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(139, 92, 246, ${clickIndicator.opacity})`;
      ctx.fill();
      ctx.restore();
    }
  }

  // Visual Click Ripple Indicator
  function showClickIndicator(x, y) {
    clickIndicator = { x, y, radius: 10, opacity: 1.0 };
    redrawCanvas();
    if (clickIndicatorTimer) clearInterval(clickIndicatorTimer);
    let step = 0;
    clickIndicatorTimer = setInterval(() => {
      step++;
      if (clickIndicator) {
        clickIndicator.radius += 3.0;
        clickIndicator.opacity -= 0.12;
        if (clickIndicator.opacity <= 0 || step >= 10) {
          clearInterval(clickIndicatorTimer);
          clickIndicator = null;
        }
        redrawCanvas();
      }
    }, 40);
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

  // Color Selection Mode Switching (Click vs Box)
  if (btnColorModeClick && btnColorModeBox) {
    btnColorModeClick.addEventListener('click', () => {
      colorMode = 'click';
      btnColorModeClick.classList.add('active');
      btnColorModeBox.classList.remove('active');
      if (colorTipCard) {
        colorTipCard.innerHTML = '👉 <strong>طريقة الاستعمال:</strong> كليكي مباشرة على أي عنصر (مثلثة، تفاحة، عصفور، قميجة...) باش تبدل لونو بدقة بدون ما يقيس الخلفية!';
      }
      clearSelection();
    });

    btnColorModeBox.addEventListener('click', () => {
      colorMode = 'box';
      btnColorModeBox.classList.add('active');
      btnColorModeClick.classList.remove('active');
      if (colorTipCard) {
        colorTipCard.innerHTML = '👉 <strong>طريقة الاستعمال:</strong> جر مربع بالماوس حول أي عنصر كامل (كلب، طيارة ورقية، دراجة...) باش تبدل لونو كامل فمرة واحدة بدون أي تأثير على باقي الصورة!';
      }
      clearSelection();
    });
  }

  // Tolerance Slider
  toleranceSlider.addEventListener('input', (e) => {
    tolerance = parseInt(e.target.value);
    toleranceVal.textContent = tolerance;
  });

  // Brush Sizing & Presets
  function setBrushSize(size) {
    brushSize = size;
    if (brushSizeSlider) brushSizeSlider.value = size;
    if (brushSizeVal) brushSizeVal.textContent = `${size}px`;
    sizePresetBtns.forEach(b => {
      b.classList.toggle('active', parseInt(b.dataset.size) === size);
    });
    redrawCanvas();
  }

  sizePresetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const size = parseInt(btn.dataset.size);
      setBrushSize(size);
    });
  });

  if (brushSizeSlider) {
    brushSizeSlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      brushSize = val;
      if (brushSizeVal) brushSizeVal.textContent = `${brushSize}px`;
      sizePresetBtns.forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.size) === val);
      });
      redrawCanvas();
    });
  }

  // Eraser Sub-Mode Switching (Brush vs Box)
  if (btnEraseModeBrush && btnEraseModeBox) {
    btnEraseModeBrush.addEventListener('click', () => {
      eraseMode = 'brush';
      btnEraseModeBrush.classList.add('active');
      btnEraseModeBox.classList.remove('active');
      if (eraseBrushControls) eraseBrushControls.style.display = 'block';
      if (eraseTipCard) {
        eraseTipCard.innerHTML = '👉 <strong>طريقة الاستعمال:</strong> دوز الممسحة فوق العنصر (عصفور، سحابة، تفاحة...) وغايتمسح بالخلفية بدون أي أثر أو تشويه!';
      }
      clearSelection();
    });

    btnEraseModeBox.addEventListener('click', () => {
      eraseMode = 'box';
      btnEraseModeBox.classList.add('active');
      btnEraseModeBrush.classList.remove('active');
      if (eraseBrushControls) eraseBrushControls.style.display = 'none';
      if (eraseTipCard) {
        eraseTipCard.innerHTML = '👉 <strong>طريقة الاستعمال:</strong> جر مربع بالماوس حول أي عنصر باغي تمسحه وغايتمسح فوراً بالخلفية بدون تشويه!';
      }
      clearSelection();
    });
  }

  // Auto-Apply Toggle
  if (eraseAutoApplyToggle) {
    eraseAutoApply = eraseAutoApplyToggle.checked;
    eraseAutoApplyToggle.addEventListener('change', (e) => {
      eraseAutoApply = e.target.checked;
      btnApplyErase.style.display = eraseAutoApply ? 'none' : 'block';
    });
    btnApplyErase.style.display = eraseAutoApply ? 'none' : 'block';
  }

  // Clear Brush/Selection
  function clearSelection() {
    isInteracting = false;
    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
    hasBrushStroke = false;
    currentBox = null;
    brushCursorPos = null;
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

    const pt = getImgCoords(e);
    startX = pt.x;
    startY = pt.y;

    if (currentTool === 'clone' && cloneState === 'paste_target') {
      // In paste mode, mousedown is a single click to paste, NOT dragging a box
      isInteracting = false;
      return;
    }

    isInteracting = true;

    if (currentTool === 'color') {
      if (colorMode === 'box') {
        currentBox = { x: pt.x, y: pt.y, w: 0, h: 0 };
        redrawCanvas();
      }
    } else if (currentTool === 'erase') {
      if (eraseMode === 'brush') {
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
      } else {
        currentBox = { x: pt.x, y: pt.y, w: 0, h: 0 };
        redrawCanvas();
      }
    } else if (currentTool === 'flip' || (currentTool === 'clone' && cloneState === 'select_source')) {
      currentBox = { x: pt.x, y: pt.y, w: 0, h: 0 };
      redrawCanvas();
    }
  });

  interactiveCanvas.addEventListener('mousemove', (e) => {
    const pt = getImgCoords(e);

    if (currentTool === 'erase' && eraseMode === 'brush') {
      brushCursorPos = pt;
    }

    if (currentTool === 'clone' && cloneState === 'paste_target') {
      clonePreviewPos = pt;
      redrawCanvas();
      return;
    }

    if (isInteracting && !isPanMode && !isSpacePressed) {
      if (currentTool === 'erase') {
        if (eraseMode === 'brush') {
          maskCtx.fillStyle = 'rgba(244, 63, 94, 0.65)';
          maskCtx.strokeStyle = 'rgba(244, 63, 94, 0.65)';
          maskCtx.lineWidth = brushSize;
          maskCtx.lineCap = 'round';
          maskCtx.lineJoin = 'round';
          maskCtx.beginPath();
          maskCtx.moveTo(startX, startY);
          maskCtx.lineTo(pt.x, pt.y);
          maskCtx.stroke();
          startX = pt.x;
          startY = pt.y;
          redrawCanvas();
        } else {
          currentBox = {
            x: Math.min(startX, pt.x),
            y: Math.min(startY, pt.y),
            w: Math.abs(pt.x - startX),
            h: Math.abs(pt.y - startY)
          };
          redrawCanvas();
        }
      } else if (
        (currentTool === 'color' && colorMode === 'box') ||
        currentTool === 'flip' ||
        (currentTool === 'clone' && cloneState === 'select_source')
      ) {
        currentBox = {
          x: Math.min(startX, pt.x),
          y: Math.min(startY, pt.y),
          w: Math.abs(pt.x - startX),
          h: Math.abs(pt.y - startY)
        };
        redrawCanvas();
      }
    } else {
      if (currentTool === 'erase' && eraseMode === 'brush') {
        redrawCanvas();
      }
    }
  });

  interactiveCanvas.addEventListener('mouseleave', () => {
    brushCursorPos = null;
    redrawCanvas();
  });

  interactiveCanvas.addEventListener('mouseup', async (e) => {
    if (isPanMode || isSpacePressed) return;
    const pt = getImgCoords(e);

    if (currentTool === 'clone' && cloneState === 'paste_target') {
      isInteracting = false;
      currentBox = null;
      const srcBox = cloneSourceBox;
      if (srcBox) {
        await applyClone(srcBox, pt.x, pt.y);
      }
      return;
    }

    if (!isInteracting) return;
    isInteracting = false;

    if (currentTool === 'color') {
      if (colorMode === 'box') {
        if (currentBox && currentBox.w > 6 && currentBox.h > 6) {
          await applyColorSwap(null, null, currentBox);
        }
      } else {
        await applyColorSwap(pt.x, pt.y, null);
      }
    } else if (currentTool === 'erase') {
      if (eraseMode === 'brush') {
        if (hasBrushStroke && eraseAutoApply) {
          await applyEraseMask();
        }
      } else if (eraseMode === 'box' && currentBox && currentBox.w > 6 && currentBox.h > 6) {
        if (eraseAutoApply) {
          await applyEraseBox(currentBox);
        }
      }
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

  window.addEventListener('mouseup', () => {
    if (isInteracting && !isPanMode && !isSpacePressed) {
      isInteracting = false;
      redrawCanvas();
    }
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      isInteracting = false;
      currentBox = null;
      if (currentTool === 'clone') {
        resetCloneTool();
      } else {
        clearSelection();
      }
    }
  });

  function resetCloneTool() {
    isInteracting = false;
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
    isInteracting = false;
    currentBox = null;
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
      setStatus('تم تكرار العنصر بنجاح!');
    } catch (err) {
      console.error(err);
      resetCloneTool();
      setStatus('Error duplicating item', false);
    } finally {
      isInteracting = false;
      currentBox = null;
      redrawCanvas();
    }
  }

  // Color Swap Action
  async function applyColorSwap(clickX, clickY, box = null) {
    setStatus('Changing color with outline precision...', true);
    if (clickX !== null && clickY !== null) {
      showClickIndicator(clickX, clickY);
    }
    try {
      const payload = {
        preset: selectedColor,
        tolerance: tolerance
      };
      if (box) {
        payload.bbox = [box.x, box.y, box.w, box.h];
      } else {
        payload.click_x = clickX;
        payload.click_y = clickY;
      }
      const res = await fetch('/api/change-color', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Color changed successfully!');
    } catch (err) {
      console.error(err);
      setStatus('Error modifying color', false);
    }
  }

  // Erase Actions
  async function applyEraseMask() {
    if (!hasBrushStroke) {
      alert('المرجو الرسم فوق العنصر المراد مسحه أولاً!');
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
  }

  async function applyEraseBox(box) {
    if (!box || box.w < 6 || box.h < 6) return;
    setStatus('Erasing area with background healing...', true);

    try {
      const res = await fetch('/api/erase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bbox: [box.x, box.y, box.w, box.h] })
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Object erased cleanly!');
    } catch (err) {
      console.error(err);
      setStatus('Error erasing object', false);
    }
  }

  btnApplyErase.addEventListener('click', async () => {
    if (eraseMode === 'box') {
      if (currentBox && currentBox.w > 6 && currentBox.h > 6) {
        await applyEraseBox(currentBox);
      } else {
        alert('المرجو جر مربع حول العنصر أولاً!');
      }
    } else {
      if (hasBrushStroke) {
        await applyEraseMask();
      } else {
        alert('المرجو الرسم فوق العنصر أولاً!');
      }
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

  // Keyboard shortcuts: Space for pan, [ and ] for brush size
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target === document.body && !isSpacePressed) {
      isSpacePressed = true;
      canvasViewport.classList.add('pan-active');
    } else if (currentTool === 'erase' && (e.target === document.body || e.target === interactiveCanvas)) {
      if (e.key === '[') {
        setBrushSize(Math.max(8, brushSize - 10));
      } else if (e.key === ']') {
        setBrushSize(Math.min(180, brushSize + 10));
      }
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
