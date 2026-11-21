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

  // Header & Production Progress Widgets
  const targetDiffsBadge = document.getElementById('targetDiffsBadge');
  const progressCompletedCount = document.getElementById('progressCompletedCount');
  const progressTotalCount = document.getElementById('progressTotalCount');
  const progressPercentBadge = document.getElementById('progressPercentBadge');
  const progressBarFill = document.getElementById('progressBarFill');

  // Multi-Puzzle & Production Queue Elements
  const stripCount = document.getElementById('stripCount');
  const stripBatchInput = document.getElementById('stripBatchInput');
  const stripAddSampleBtn = document.getElementById('stripAddSampleBtn');
  const stripClearAllBtn = document.getElementById('stripClearAllBtn');
  const pagesTrack = document.getElementById('pagesTrack');
  const kdpSolutionsPerPage = document.getElementById('kdpSolutionsPerPage');
  const chkBelongsTo = document.getElementById('chkBelongsTo');
  const chkInstructions = document.getElementById('chkInstructions');
  const chkCertificate = document.getElementById('chkCertificate');
  const summaryTotalPuzzles = document.getElementById('summaryTotalPuzzles');
  const summaryTotalDiffs = document.getElementById('summaryTotalDiffs');
  const summaryCompletedPuzzles = document.getElementById('summaryCompletedPuzzles');
  const summaryPendingPuzzles = document.getElementById('summaryPendingPuzzles');
  const summaryEstPages = document.getElementById('summaryEstPages');
  const kdpTargetDiffs = document.getElementById('kdpTargetDiffs');
  const chkOnlyCompletedPdf = document.getElementById('chkOnlyCompletedPdf');

  // Workflow Navigation & Auto-Advance Elements
  const btnPrevPuzzle = document.getElementById('btnPrevPuzzle');
  const btnNextPendingPuzzle = document.getElementById('btnNextPendingPuzzle');
  const chkAutoAdvance = document.getElementById('chkAutoAdvance');
  const tabFilterQueue = document.getElementById('tabFilterQueue');
  const tabFilterCompleted = document.getElementById('tabFilterCompleted');
  const tabFilterAll = document.getElementById('tabFilterAll');
  const filterQueueCount = document.getElementById('filterQueueCount');
  const filterCompletedCount = document.getElementById('filterCompletedCount');
  const filterAllCount = document.getElementById('filterAllCount');

  // Celebration Toast Elements
  const completionToast = document.getElementById('completionToast');
  const toastTitle = document.getElementById('toastTitle');
  const toastDesc = document.getElementById('toastDesc');
  const btnStayCurrent = document.getElementById('btnStayCurrent');

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

  let currentFilter = 'queue'; // 'queue' (pending) | 'completed' | 'all'
  let autoAdvanceTimer = null;
  let lastCompletedPuzzleId = null;
  let targetDifferences = 5;
  let lastKnownPuzzles = [];
  let lastKnownBook = null;

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

  // Toast Celebration & Notification
  function showCelebrationToast(title, desc, autoNextMs = 0) {
    if (!completionToast) return;
    if (toastTitle) toastTitle.textContent = title;
    if (toastDesc) toastDesc.textContent = desc;
    completionToast.classList.remove('hidden');

    if (autoAdvanceTimer) {
      clearTimeout(autoAdvanceTimer);
      autoAdvanceTimer = null;
    }

    if (autoNextMs > 0) {
      autoAdvanceTimer = setTimeout(async () => {
        hideCelebrationToast();
        await goToNextPendingPuzzle();
      }, autoNextMs);
    }
  }

  function hideCelebrationToast() {
    if (completionToast) {
      completionToast.classList.add('hidden');
    }
    if (autoAdvanceTimer) {
      clearTimeout(autoAdvanceTimer);
      autoAdvanceTimer = null;
    }
  }

  // Render Book Pages Strip & Summary
  function renderBookStrip(book, puzzles) {
    if (!puzzles || !pagesTrack) return;
    lastKnownPuzzles = puzzles;
    if (book) lastKnownBook = book;
    const target = (book && book.target_differences) ? book.target_differences : targetDifferences;
    targetDifferences = target;

    // Filter counts
    const completedPuzzles = puzzles.filter(p => (p.diff_count >= target || p.is_completed));
    const queuePuzzles = puzzles.filter(p => (p.diff_count < target && !p.is_completed));

    if (filterQueueCount) filterQueueCount.textContent = queuePuzzles.length;
    if (filterCompletedCount) filterCompletedCount.textContent = completedPuzzles.length;
    if (filterAllCount) filterAllCount.textContent = puzzles.length;
    if (stripCount) stripCount.textContent = puzzles.length;

    // Filter display list
    let displayList = [];
    if (currentFilter === 'queue') {
      displayList = queuePuzzles;
    } else if (currentFilter === 'completed') {
      displayList = completedPuzzles;
    } else {
      displayList = puzzles;
    }

    if (displayList.length === 0) {
      if (currentFilter === 'queue') {
        if (puzzles.length > 0 && completedPuzzles.length === puzzles.length) {
          pagesTrack.innerHTML = `
            <div class="strip-empty-state success">
              <span style="font-size:1.4rem;">🎉</span>
              <span>جميع الصور مكتملة بنجاح (100%)! تم حفظها فـ تبويب "المكتملة للـ PDF" وكتابك جاهز للتحميل.</span>
            </div>
          `;
        } else {
          pagesTrack.innerHTML = `
            <div class="strip-empty-state">
              <span>📭</span>
              <span>لا توجد صور قيد العمل. اضغط على "رفع عدة صور" للبدء في كتاب جديد.</span>
            </div>
          `;
        }
      } else if (currentFilter === 'completed') {
        pagesTrack.innerHTML = `
          <div class="strip-empty-state">
            <span>⏳</span>
            <span>لم تكتمل أي صورة بعد. أكمل ${target} تعديلات على أي صورة لتنتقل إلى هنا تلقائياً وتُحفظ للـ PDF.</span>
          </div>
        `;
      } else {
        pagesTrack.innerHTML = `
          <div class="strip-empty-state">
            <span>📁</span>
            <span>لم تقم بإضافة أي صور بعد.</span>
          </div>
        `;
      }
    } else {
      pagesTrack.innerHTML = displayList.map(p => {
        const isDone = (p.diff_count >= target || p.is_completed);
        let badgeClass = 'empty';
        let badgeText = `${p.diff_count}/${target}`;
        if (isDone) {
          badgeClass = 'ready';
          badgeText = `✅ ${p.diff_count} diffs`;
        } else if (p.diff_count > 0) {
          badgeClass = 'pending';
          badgeText = `⏳ ${p.diff_count}/${target}`;
        }

        return `
          <div class="puzzle-thumb-card ${p.is_active ? 'active' : ''} ${isDone ? 'completed-card' : ''}" data-puzzle-id="${p.id}" title="${p.title}">
            <img class="puzzle-thumb-img" src="${p.thumb_url}" alt="Puzzle ${p.id}" loading="lazy">
            <div class="puzzle-card-info">
              <span class="puzzle-card-num">#${p.id}</span>
              <span class="puzzle-card-badge ${badgeClass}">${badgeText}</span>
            </div>
            ${puzzles.length > 1 ? `<button class="puzzle-card-delete" data-delete-id="${p.id}" title="حذف هذا اللغز">×</button>` : ''}
          </div>
        `;
      }).join('');

      // Attach click listeners to cards
      pagesTrack.querySelectorAll('.puzzle-thumb-card').forEach(card => {
        card.addEventListener('click', async (e) => {
          if (e.target.closest('.puzzle-card-delete')) return;
          const pId = parseInt(card.dataset.puzzleId);
          await selectPuzzle(pId);
        });
      });

      // Attach click listeners to delete buttons
      pagesTrack.querySelectorAll('.puzzle-card-delete').forEach(delBtn => {
        delBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const pId = parseInt(delBtn.dataset.deleteId);
          if (confirm(`هل أنت متأكد من حذف اللغز #${pId}؟`)) {
            await deletePuzzle(pId);
          }
        });
      });
    }

    updateBookSummary(book, puzzles);
  }

  function updateBookSummary(book, puzzles) {
    if (!puzzles) return;
    const target = (book && book.target_differences) ? book.target_differences : targetDifferences;
    const totalPuzzles = puzzles.length;
    const completedCount = puzzles.filter(p => (p.diff_count >= target || p.is_completed)).length;
    const pendingCount = totalPuzzles - completedCount;
    const progressPct = totalPuzzles > 0 ? Math.round((completedCount / totalPuzzles) * 100) : 0;

    // Header progress widgets
    if (progressCompletedCount) progressCompletedCount.textContent = completedCount;
    if (progressTotalCount) progressTotalCount.textContent = totalPuzzles;
    if (progressPercentBadge) progressPercentBadge.textContent = `${progressPct}%`;
    if (progressBarFill) progressBarFill.style.width = `${progressPct}%`;

    // Right sidebar summary stats
    if (summaryTotalPuzzles) summaryTotalPuzzles.textContent = totalPuzzles;
    if (summaryCompletedPuzzles) summaryCompletedPuzzles.textContent = completedCount;
    if (summaryPendingPuzzles) summaryPendingPuzzles.textContent = pendingCount;
    if (summaryTotalDiffs) {
      summaryTotalDiffs.textContent = puzzles.reduce((sum, p) => sum + (p.diff_count || 0), 0);
    }

    const hasBelongs = chkBelongsTo ? chkBelongsTo.checked : (book ? book.include_belongs_to : true);
    const hasInstr = chkInstructions ? chkInstructions.checked : (book ? book.include_instructions : true);
    const hasCert = chkCertificate ? chkCertificate.checked : (book ? book.include_certificate : true);
    const solsPerPg = kdpSolutionsPerPage ? parseInt(kdpSolutionsPerPage.value) : 4;
    const onlyComp = chkOnlyCompletedPdf ? chkOnlyCompletedPdf.checked : true;

    const effectivePuzzles = onlyComp ? (completedCount > 0 ? completedCount : totalPuzzles) : totalPuzzles;
    const frontPages = (hasBelongs ? 1 : 0) + (hasInstr ? 1 : 0);
    const certPages = hasCert ? 1 : 0;
    const solPages = solsPerPg === 4 ? Math.ceil(effectivePuzzles / 4) : effectivePuzzles;
    const estPages = frontPages + effectivePuzzles + solPages + certPages;

    if (summaryEstPages) summaryEstPages.textContent = `${estPages} Pages (300 DPI)`;
    if (btnExportFullPdf) {
      btnExportFullPdf.innerHTML = `📕 تحميل الكتاب كامل (PDF 300 DPI) [${effectivePuzzles} لغز]`;
    }
  }

  // Select Puzzle
  async function selectPuzzle(puzzleId) {
    setStatus(`Loading Puzzle #${puzzleId}...`, true);
    try {
      const res = await fetch('/api/book/select-puzzle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ puzzle_id: puzzleId })
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus(`Puzzle #${puzzleId} loaded.`);
    } catch (err) {
      console.error(err);
      setStatus('Failed to switch puzzle', false);
    }
  }

  // Next Pending Puzzle (Auto-Queue)
  async function goToNextPendingPuzzle() {
    setStatus('Loading next pending puzzle...', true);
    try {
      const res = await fetch('/api/book/next-pending', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      if (data.book && data.book.pending_count === 0) {
        showCelebrationToast('🎉 تهانينا! جميع صور الكتاب مكتملة!', 'تم إنجاز 100% من الألغاز. يمكنك الآن تحميل كتاب الـ PDF كامل.');
      } else {
        setStatus(`Switched to Puzzle #${data.active_puzzle.id}`);
      }
    } catch (err) {
      console.error(err);
      setStatus('Failed to switch puzzle', false);
    }
  }

  // Previous Puzzle
  async function goToPrevPuzzle() {
    setStatus('Loading previous puzzle...', true);
    try {
      const res = await fetch('/api/book/prev-puzzle', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus(`Switched to Puzzle #${data.active_puzzle.id}`);
    } catch (err) {
      console.error(err);
      setStatus('Failed to switch puzzle', false);
    }
  }

  // Delete Puzzle
  async function deletePuzzle(puzzleId) {
    setStatus(`Deleting Puzzle #${puzzleId}...`, true);
    try {
      const res = await fetch('/api/book/delete-puzzle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ puzzle_id: puzzleId })
      });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus(`Puzzle #${puzzleId} deleted.`);
    } catch (err) {
      console.error(err);
      setStatus('Failed to delete puzzle', false);
    }
  }

  // Batch Upload Handling
  async function handleBatchUpload(fileList) {
    if (!fileList || fileList.length === 0) return;
    setStatus(`Uploading ${fileList.length} image(s)...`, true);
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }
    try {
      const res = await fetch('/api/book/upload-batch', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      // Automatically switch to queue tab so user sees all pending images
      currentFilter = 'queue';
      if (tabFilterQueue) tabFilterQueue.classList.add('active');
      if (tabFilterCompleted) tabFilterCompleted.classList.remove('active');
      if (tabFilterAll) tabFilterAll.classList.remove('active');

      clearSelection();
      updateStateUI(data);
      setStatus(`${fileList.length} image(s) added to production queue!`);
    } catch (err) {
      console.error(err);
      setStatus('Batch upload failed', false);
    }
  }

  // Update State UI
  function updateStateUI(state) {
    const target = (state.book && state.book.target_differences) ? state.book.target_differences : targetDifferences;
    targetDifferences = target;

    if (diffCountBadge) diffCountBadge.textContent = state.differences_count;
    if (targetDiffsBadge) targetDiffsBadge.textContent = target;
    if (diffTotal) diffTotal.textContent = state.differences_count;
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

    // Check for Completion & Auto-Advance
    const isCompleted = state.differences_count >= target;
    if (isCompleted && lastCompletedPuzzleId !== state.active_puzzle.id) {
      lastCompletedPuzzleId = state.active_puzzle.id;
      const isAutoAdv = chkAutoAdvance ? chkAutoAdvance.checked : true;
      const hasMorePending = state.book && state.book.pending_count > 0;

      if (hasMorePending) {
        if (isAutoAdv) {
          showCelebrationToast(
            `🎉 لغز #${state.active_puzzle.id} مكتمل (${state.differences_count}/${target})!`,
            `تم الحفظ والنقل إلى "المكتملة للـ PDF". جاري الانتقال للصورة الموالية تلقائياً...`,
            1200
          );
        } else {
          showCelebrationToast(
            `🎉 لغز #${state.active_puzzle.id} مكتمل (${state.differences_count}/${target})!`,
            `تم الحفظ والنقل إلى "المكتملة للـ PDF". يمكنك الانتقال للصورة الموالية وقتما تشاء.`,
            0
          );
        }
      } else {
        showCelebrationToast(
          `🎉 تهانينا! جميع صور الكتاب مكتملة!`,
          `تم إنجاز جميع الألغاز بنجاح (${state.book.total_puzzles}/${state.book.total_puzzles}). كتابك جاهز الآن للتحميل الكامل كـ PDF.`,
          0
        );
      }
    } else if (!isCompleted && lastCompletedPuzzleId === state.active_puzzle.id) {
      // If user undid a difference and dropped below target, reset lastCompletedPuzzleId
      lastCompletedPuzzleId = null;
      hideCelebrationToast();
    }

    // Render Filmstrip & Summary
    if (state.puzzles) {
      renderBookStrip(state.book, state.puzzles);
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
    if (!confirm('Are you sure you want to reset all differences for this puzzle?')) return;
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

  // Load Sample Button in Header
  btnLoadSample.addEventListener('click', async () => {
    setStatus('Adding sample puzzle...', true);
    try {
      const res = await fetch('/api/load-sample', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('Sample park puzzle added.');
    } catch (err) {
      console.error(err);
    }
  });

  // Strip Sample Add Button
  if (stripAddSampleBtn) {
    stripAddSampleBtn.addEventListener('click', async () => {
      setStatus('Adding sample puzzle...', true);
      try {
        const res = await fetch('/api/book/add-sample', { method: 'POST' });
        const data = await res.json();
        clearSelection();
        updateStateUI(data);
        setStatus('Sample park puzzle added to book.');
      } catch (err) {
        console.error(err);
      }
    });
  }

  // Strip 1-Click Clear All Button
  const handleClearAllAction = async () => {
    const confirmed = confirm('هل أنت متأكد من مسح جميع الصور في الكتاب والبدء من جديد بضغطة واحدة؟');
    if (!confirmed) return;
    setStatus('Clearing all book puzzles...', true);
    try {
      const res = await fetch('/api/book/clear-all', { method: 'POST' });
      const data = await res.json();
      clearSelection();
      updateStateUI(data);
      setStatus('All puzzles cleared successfully. Ready for new images.');
    } catch (err) {
      console.error(err);
      setStatus('Failed to clear puzzles.', false);
    }
  };

  if (stripClearAllBtn) {
    stripClearAllBtn.addEventListener('click', handleClearAllAction);
  }

  const btnSideClearAll = document.getElementById('btnSideClearAll');
  if (btnSideClearAll) {
    btnSideClearAll.addEventListener('click', handleClearAllAction);
  }

  // Multi-Image Upload inputs
  fileUploadInput.addEventListener('change', async (e) => {
    await handleBatchUpload(e.target.files);
    e.target.value = '';
  });

  if (stripBatchInput) {
    stripBatchInput.addEventListener('change', async (e) => {
      await handleBatchUpload(e.target.files);
      e.target.value = '';
    });
  }

  // Summary recalculation on config toggles
  [chkBelongsTo, chkInstructions, chkCertificate, kdpSolutionsPerPage].forEach(el => {
    if (el) {
      el.addEventListener('change', () => {
        // Trigger live summary recalculation
        fetchState();
      });
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
          title: kdpTitle ? kdpTitle.value : 'SPOT THE DIFFERENCES!',
          page_size: kdpPageSize ? kdpPageSize.value : '8.5x8.5'
        })
      });
      const blob = await res.blob();
      downloadBlob(blob, `KDP_Puzzle_Page_300DPI.png`);
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
          page_size: kdpPageSize ? kdpPageSize.value : '8.5x8.5'
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
          title: kdpTitle ? kdpTitle.value : 'SPOT THE DIFFERENCES!',
          page_size: kdpPageSize ? kdpPageSize.value : '8.5x8.5',
          include_belongs_to: chkBelongsTo ? chkBelongsTo.checked : true,
          include_instructions: chkInstructions ? chkInstructions.checked : true,
          include_certificate: chkCertificate ? chkCertificate.checked : true,
          solutions_per_page: kdpSolutionsPerPage ? parseInt(kdpSolutionsPerPage.value) : 4,
          only_completed: chkOnlyCompletedPdf ? chkOnlyCompletedPdf.checked : true
        })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || 'Export PDF returned error status');
      }
      const blob = await res.blob();
      downloadBlob(blob, 'Spot_The_Differences_Book_300DPI.pdf');
      setStatus('Complete PDF Book downloaded!');
    } catch (err) {
      console.error(err);
      alert(err.message || 'Error generating PDF. Please ensure at least one puzzle has differences.');
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

  // --- Smart Queue Filter Tabs Event Listeners ---
  if (tabFilterQueue) {
    tabFilterQueue.addEventListener('click', () => {
      currentFilter = 'queue';
      tabFilterQueue.classList.add('active');
      if (tabFilterCompleted) tabFilterCompleted.classList.remove('active');
      if (tabFilterAll) tabFilterAll.classList.remove('active');
      renderBookStrip(lastKnownBook, lastKnownPuzzles);
    });
  }

  if (tabFilterCompleted) {
    tabFilterCompleted.addEventListener('click', () => {
      currentFilter = 'completed';
      tabFilterCompleted.classList.add('active');
      if (tabFilterQueue) tabFilterQueue.classList.remove('active');
      if (tabFilterAll) tabFilterAll.classList.remove('active');
      renderBookStrip(lastKnownBook, lastKnownPuzzles);
    });
  }

  if (tabFilterAll) {
    tabFilterAll.addEventListener('click', () => {
      currentFilter = 'all';
      tabFilterAll.classList.add('active');
      if (tabFilterQueue) tabFilterQueue.classList.remove('active');
      if (tabFilterCompleted) tabFilterCompleted.classList.remove('active');
      renderBookStrip(lastKnownBook, lastKnownPuzzles);
    });
  }

  // Target Differences Setting
  if (kdpTargetDiffs) {
    kdpTargetDiffs.addEventListener('change', async () => {
      const newTarget = parseInt(kdpTargetDiffs.value);
      targetDifferences = newTarget;
      try {
        const res = await fetch('/api/book/update-config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_differences: newTarget })
        });
        const data = await res.json();
        updateStateUI(data);
      } catch (err) {
        console.error(err);
      }
    });
  }

  // Safe PDF Toggle
  if (chkOnlyCompletedPdf) {
    chkOnlyCompletedPdf.addEventListener('change', () => {
      updateBookSummary(lastKnownBook, lastKnownPuzzles);
    });
  }

  // Quick Workflow Navigation Buttons
  if (btnNextPendingPuzzle) {
    btnNextPendingPuzzle.addEventListener('click', () => {
      hideCelebrationToast();
      goToNextPendingPuzzle();
    });
  }

  if (btnPrevPuzzle) {
    btnPrevPuzzle.addEventListener('click', () => {
      hideCelebrationToast();
      goToPrevPuzzle();
    });
  }

  // Toast Stay Button
  if (btnStayCurrent) {
    btnStayCurrent.addEventListener('click', () => {
      hideCelebrationToast();
    });
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
    const panBtnText = document.getElementById('panBtnText');
    btnPanToggle.addEventListener('click', () => {
      isPanMode = !isPanMode;
      btnPanToggle.classList.toggle('active', isPanMode);
      canvasViewport.classList.toggle('pan-active', isPanMode);
      if (isPanMode) {
        if (panBtnText) panBtnText.textContent = '✋ وضع التحريك (Pan: ON)';
        setStatus('✋ وضع التحريك شغال: جر بالماوس باش تحرك الصورة فـ الكانفاس');
      } else {
        if (panBtnText) panBtnText.textContent = '✋ تحريك الصفحة (Pan)';
        setStatus('🎯 وضع النقر والتعديل شغال: كليكي مباشرة على الصورة');
      }
    });
  }

  // Keyboard shortcuts: Space for pan, [ and ] for brush size
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target === document.body && !isSpacePressed) {
      isSpacePressed = true;
      canvasViewport.classList.add('pan-active');
      if (btnPanToggle) btnPanToggle.classList.add('active');
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
        if (btnPanToggle) btnPanToggle.classList.remove('active');
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

  // -------------------------------------------------------------------------
  // KDP AI PROMPT STUDIO (Winter / Christmas & Custom Niches)
  // -------------------------------------------------------------------------
  const btnOpenPromptModal = document.getElementById('btnOpenPromptModal');
  const btnClosePromptModal = document.getElementById('btnClosePromptModal');
  const promptModal = document.getElementById('promptModal');

  const promptNicheSelect = document.getElementById('promptNicheSelect');
  const promptModelSelect = document.getElementById('promptModelSelect');
  const promptArSelect = document.getElementById('promptArSelect');
  const promptCustomCount = document.getElementById('promptCustomCount');
  const countPresetBtns = document.querySelectorAll('.count-preset-btn');

  const btnGeneratePrompts = document.getElementById('btnGeneratePrompts');
  const promptResultsCount = document.getElementById('promptResultsCount');
  const promptSearchInput = document.getElementById('promptSearchInput');
  const promptCardsContainer = document.getElementById('promptCardsContainer');

  const btnCopyAllPrompts = document.getElementById('btnCopyAllPrompts');
  const btnDownloadPromptsTxt = document.getElementById('btnDownloadPromptsTxt');
  const btnDownloadPromptsCsv = document.getElementById('btnDownloadPromptsCsv');

  let currentPromptsList = [];

  // Open / Close Modal
  if (btnOpenPromptModal) {
    btnOpenPromptModal.addEventListener('click', () => {
      promptModal.classList.remove('hidden');
    });
  }

  if (btnClosePromptModal) {
    btnClosePromptModal.addEventListener('click', () => {
      promptModal.classList.add('hidden');
    });
  }

  // Close on outside click
  if (promptModal) {
    promptModal.addEventListener('click', (e) => {
      if (e.target === promptModal) {
        promptModal.classList.add('hidden');
      }
    });
  }

  // Close on Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && promptModal && !promptModal.classList.contains('hidden')) {
      promptModal.classList.add('hidden');
    }
  });

  // Count Presets
  countPresetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      countPresetBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const val = parseInt(btn.dataset.count);
      if (promptCustomCount) promptCustomCount.value = val;
      if (btnGeneratePrompts) {
        btnGeneratePrompts.textContent = `✨ توليد ${val} برومت فـ دقة وحدة`;
      }
    });
  });

  if (promptCustomCount) {
    promptCustomCount.addEventListener('input', () => {
      const val = parseInt(promptCustomCount.value) || 50;
      countPresetBtns.forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.count) === val);
      });
      if (btnGeneratePrompts) {
        btnGeneratePrompts.textContent = `✨ توليد ${val} برومت فـ دقة وحدة`;
      }
    });
  }

  // Generate Prompts Action
  if (btnGeneratePrompts) {
    btnGeneratePrompts.addEventListener('click', async () => {
      const niche = promptNicheSelect ? promptNicheSelect.value : 'winter_christmas';
      const count = promptCustomCount ? (parseInt(promptCustomCount.value) || 50) : 50;
      const targetModel = promptModelSelect ? promptModelSelect.value : 'midjourney';
      const ar = promptArSelect ? promptArSelect.value : '1:1';

      btnGeneratePrompts.disabled = true;
      btnGeneratePrompts.textContent = '⏳ جاري توليد البرومتات...';
      setStatus(`Generating ${count} ${niche} prompts...`, true);

      try {
        const res = await fetch('/api/prompts/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            niche: niche,
            count: count,
            target_model: targetModel,
            aspect_ratio: ar
          })
        });

        const data = await res.json();
        currentPromptsList = data.prompts || [];
        renderPromptsList(currentPromptsList);
        setStatus(`${currentPromptsList.length} prompts generated successfully!`);
      } catch (err) {
        console.error(err);
        setStatus('Failed to generate prompts', false);
      } finally {
        btnGeneratePrompts.disabled = false;
        btnGeneratePrompts.textContent = `✨ توليد ${count} برومت فـ دقة وحدة`;
      }
    });
  }

  // Render Prompt Cards
  function renderPromptsList(prompts) {
    if (!promptCardsContainer) return;
    if (promptResultsCount) promptResultsCount.textContent = prompts.length;

    if (prompts.length === 0) {
      promptCardsContainer.innerHTML = `
        <div class="prompt-empty-state">
          <span>🔍</span>
          <h3>لا توجد نتائج تطابق بحثك</h3>
          <p>جرب كتابة كلمات أخرى أو امسح شريط البحث.</p>
        </div>
      `;
      return;
    }

    promptCardsContainer.innerHTML = prompts.map(p => `
      <div class="prompt-result-card" data-prompt-id="${p.id}">
        <div class="card-top-row">
          <div class="card-title-group">
            <span class="card-num-badge">#${p.id}</span>
            <span class="card-title">${p.title}</span>
          </div>
          <button class="btn-copy-card" data-copy-text="${encodeURIComponent(p.prompt)}">
            📋 Copy Prompt
          </button>
        </div>
        <div class="card-prompt-box">${escapeHtml(p.prompt)}</div>
        <div class="card-diffs-box">
          <span class="card-diffs-header">🎯 الفروقات المقترحة لهاد الصورة فـ Studio:</span>
          <div class="card-diffs-tags">
            ${p.suggested_differences.map(d => `<span class="diff-tag">${escapeHtml(d)}</span>`).join('')}
          </div>
        </div>
      </div>
    `).join('');

    // Attach 1-click copy listeners
    promptCardsContainer.querySelectorAll('.btn-copy-card').forEach(btn => {
      btn.addEventListener('click', async () => {
        const text = decodeURIComponent(btn.dataset.copyText);
        try {
          await navigator.clipboard.writeText(text);
          btn.textContent = '✅ Copied!';
          btn.classList.add('copied');
          setTimeout(() => {
            btn.textContent = '📋 Copy Prompt';
            btn.classList.remove('copied');
          }, 2000);
        } catch (err) {
          console.error(err);
        }
      });
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Live Search Filter
  if (promptSearchInput) {
    promptSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        renderPromptsList(currentPromptsList);
        return;
      }
      const filtered = currentPromptsList.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.prompt.toLowerCase().includes(q) ||
        p.suggested_differences.some(d => d.toLowerCase().includes(q))
      );
      renderPromptsList(filtered);
    });
  }

  // Copy All Action
  if (btnCopyAllPrompts) {
    btnCopyAllPrompts.addEventListener('click', async () => {
      if (currentPromptsList.length === 0) {
        alert('يرجى توليد البرومتات أولاً!');
        return;
      }
      const allText = currentPromptsList.map((p, i) => `Prompt #${i+1} - ${p.title}:\n${p.prompt}\n`).join('\n' + '='.repeat(40) + '\n\n');
      try {
        await navigator.clipboard.writeText(allText);
        btnCopyAllPrompts.textContent = '✅ تم نسخ جميع البرومتات!';
        setTimeout(() => {
          btnCopyAllPrompts.textContent = '📋 نسخ الكل (Copy All)';
        }, 2500);
      } catch (err) {
        console.error(err);
      }
    });
  }

  // Download TXT
  if (btnDownloadPromptsTxt) {
    btnDownloadPromptsTxt.addEventListener('click', async () => {
      if (currentPromptsList.length === 0) {
        alert('يرجى توليد البرومتات أولاً!');
        return;
      }
      try {
        const res = await fetch('/api/prompts/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            format: 'txt',
            prompts: currentPromptsList
          })
        });
        const blob = await res.blob();
        downloadBlob(blob, `KDP_Prompts_${currentPromptsList.length}.txt`);
      } catch (err) {
        console.error(err);
      }
    });
  }

  // Download CSV
  if (btnDownloadPromptsCsv) {
    btnDownloadPromptsCsv.addEventListener('click', async () => {
      if (currentPromptsList.length === 0) {
        alert('يرجى توليد البرومتات أولاً!');
        return;
      }
      try {
        const res = await fetch('/api/prompts/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            format: 'csv',
            prompts: currentPromptsList
          })
        });
        const blob = await res.blob();
        downloadBlob(blob, `KDP_Prompts_${currentPromptsList.length}.csv`);
      } catch (err) {
        console.error(err);
      }
    });
  }
});
