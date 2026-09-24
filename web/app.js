/**
 * LongCat-Video-Avatar 1.5 Studio — Multi-Slot Tabbed Web Client
 * 
 * Features:
 * - Up to 5 Video Generation Slots (Video 1, Video 2, ... Video 5)
 * - Independent Media, Configuration, Logs, and Video Players per Tab
 * - Sequential GPU Background Queue Support
 * - Real-Time Queue Monitor Modal Dashboard
 * - Fullscreen Video Previews & Advanced Batch Gallery Management
 */

const DEFAULT_POSITIVE_PROMPT = `Use the uploaded image exactly as the reference. Preserve the same man, face, hairstyle, facial hair, skin tone, clothing, body proportions, framing, lighting, and natural colors.

Professional man speaking naturally, calmly, and politely with smooth accurate lip sync, restrained natural mouth aperture, controlled gentle jaw movement, and relaxed closed mouth during pauses. Natural conversational voice cadence, steady dignified eye contact, relaxed facial expressions, and natural irregular blinking without weird staring or darting eyes.

Gentle organic breathing with subtle chest and shoulder rise and fall. Composed, dignified presenter with stable upright head posture and poised neck. Calm, polite delivery with steady centered head alignment, zero wild head shaking, zero head bobbing, zero erratic tilting, and zero side-to-side swaying. Maintain composed realistic upper-body posture without repetitive rocking or excessive gestures.

Locked stationary tripod camera. Zero zoom in, zero zoom out, no pan, no tilt, no camera shake, no forward leaning, and completely static background.

Preserve identity, facial features, beard texture, clothing, lighting, and photographic realism throughout. Natural matte masculine lips with zero lipstick or gloss, authentic skin tone matching reference photo exactly. Avoid aggressive speech, wide mouth opening, jaw stretching, robotic motion, or exaggerated facial expressions.

Final result should look like a real authentic human man speaking calmly, politely, and professionally in a high-end podcast or interview.`;

const DEFAULT_NEGATIVE_PROMPT = `Aggressive speech, shouting, yelling, loud forceful talking, wide mouth opening, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, wide jaw drop, unhinged jaw, dropped jaw, stretching jaw, loose mouth, gaping oral cavity, forced facial strain, jaw tension, clenched teeth, robotic mouth stretching, dramatic mouth movement, excessive lip flapping, wide toothy speech, popping neck veins, exaggerated head shaking, head bobbing, head swaying, head rolling, head tilting, erratic head jerks, nodding head, side-to-side head shaking, wobbling head, unstable head posture, jerky neck, neck twisting, neck stretching, neck swaying, bobblehead, wild gestures, chaotic motion, restless posture, sudden fast movements, exaggerated expressions, strange staring, darting eyes, wide eyes, artificial grimace, unnatural eye movement, AI uncanny valley look.

Moving hands while speaking, conversational hand gestures, talking with hands, gesturing with hands, raising hands to emphasize speech, hand movements synced to speech cadence or style, expressive hand gestures, repetitive hand gestures, waving hands, moving arms, hands entering frame, hands rising, fidgeting hands, touching face, touching hair, touching chest, finger distortion, extra fingers, missing fingers, deformed hands, broken wrists, unnatural hands.

Frozen body, stiff mannequin posture, robotic posture, wooden torso, artificial paralysis, frozen chest, locked shoulders.

Zoom in, zoom out, camera movement, camera drift, pan, tilt, framing shift, focal-length change, scale change, camera shake, frame vibration, jumping cuts.

Forward leaning, lunging toward camera, moving closer to camera, head pitching forward, torso leaning forward, excessive bowing.

Overexposure, washed-out colors, white haze, lifted blacks, desaturated colors, skin brightening, whitening filter, beauty filter, airbrushed skin, plastic skin, altered skin tone, bleached highlights, flat lighting, glowing teeth, teeth emitting light, white tooth glare.

Pink lips, red lips, magenta lips, lipstick, lip gloss, glossy lips, painted lips, unnatural lip color.

Face distortion, body warping, anatomy distortion, deformed features, low quality, severe artifacts, disfigured appearance.`;

const FEMALE_POSITIVE_PROMPT = `Use the uploaded image exactly as the reference. Preserve the same woman, face, hairstyle, skin tone, clothing, body proportions, framing, lighting, and natural colors.

Professional woman speaking naturally, calmly, and politely with smooth accurate lip sync, restrained natural mouth aperture, controlled gentle jaw movement, and relaxed closed lips during pauses. Natural conversational delivery, steady dignified eye gaze, relaxed facial expressions, subtle cheek motion, and natural irregular blinking.

Gentle organic breathing with subtle chest and shoulder rise and fall. Her breasts will bounce while she talks naturally, with realistic weight and soft secondary motion caused by breathing and speech. Keep it natural and never exaggerated or repetitive.

Composed, dignified presenter with stable upright head posture and poised neck. Calm, polite delivery with steady centered head alignment, zero wild head shaking, zero head bobbing, zero erratic tilting, and zero side-to-side swaying. Maintain poised realistic upper-body posture without repetitive rocking or excessive gestures.

Locked stationary tripod camera. Zero zoom in, zero zoom out, no pan, no tilt, no camera shake, no forward leaning, and completely static background.

Preserve identity, anatomy, clothing, lighting, and image consistency throughout. Avoid face distortion, body warping, chest distortion, lip jitter, robotic motion, repetitive movement, wide mouth opening, or exaggerated expressions.

Final result should look like a real professional woman speaking calmly, politely, and naturally in a high-end podcast or interview.`;

const FEMALE_NEGATIVE_PROMPT = `Aggressive speech, shouting, yelling, loud forceful talking, wide mouth opening, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, wide jaw drop, unhinged jaw, dropped jaw, stretching jaw, loose mouth, gaping oral cavity, forced facial strain, jaw tension, clenched teeth, robotic mouth stretching, dramatic mouth movement, excessive lip flapping, wide toothy speech, popping neck veins, exaggerated head shaking, head bobbing, head swaying, head rolling, head tilting, erratic head jerks, nodding head, side-to-side head shaking, wobbling head, unstable head posture, jerky neck, neck twisting, neck stretching, neck swaying, bobblehead, wild gestures, chaotic motion, restless posture, sudden fast movements, aggressive gestures.

Moving hands while speaking, conversational hand gestures, talking with hands, gesturing with hands, raising hands to emphasize speech, hand movements synced to speech cadence or style, expressive hand gestures, repetitive hand gestures, waving hands, moving arms, hands entering frame, touching hair, face, or chest, excessive hand movement, finger distortion, extra or missing fingers, fused or deformed fingers, broken wrists, unnatural hands, ring morphing or flickering, changing nail color, nail morphing.

Frozen body, stiff mannequin posture, robotic posture, wooden torso, artificial paralysis, frozen chest, locked shoulders.

Zoom in, zoom out, camera movement, camera drift, pan, tilt, framing shift, focal-length change, scale change, camera shake, frame vibration, jumping cuts.

Forward leaning, lunging toward camera, moving closer to camera, head pitching forward, torso leaning forward, excessive bowing.

Overexposure, washed-out colors, white haze, lifted blacks, desaturated colors, skin brightening, whitening filter, beauty filter, airbrushed skin, plastic skin, altered skin tone, bleached highlights, flat lighting.

Pink, red, magenta, purple, or violet lips, lipstick, lip gloss, glossy or shiny lips, painted lips, unnatural lip color.

Face distortion, body warping, anatomy distortion, deformed features, low quality, severe artifacts, disfigured appearance.`;

// Global Multi-Slot State
function createSlot(id, name) {
  return {
    id: id,
    name: name,
    title: '',


    imageFile: null,
    imageDataUrl: null,
    imageName: null,
    imageDimensions: null,
    imageSizeMb: null,
    imageUrl: null,
    imageAssetId: null,

    audioFile: null,
    audioDataUrl: null,
    audioName: null,
    audioDuration: 0,
    audioSizeMb: null,
    audioUrl: null,
    audioAssetId: null,
    audioLibraryFilename: null,

    selectedRatio: 'auto',
    selectedResolution: '500p',
    gender: '',
    detectedGender: '',
    detectedRatio: '9:16',
    detectedResolution: '1080x1920',
    detectedQualityLabel: 'Full HD Portrait',
    detectedRatioTitle: '9:16 Portrait (Reels / Shorts)',
    selectedPreset: 'distill_bf16',
    selectedSteps: 3,
    generationMode: 'anchor_seamless',
    numFrames: 205,
    lengthMode: 'auto',
    prompt: DEFAULT_POSITIVE_PROMPT,
    negativePrompt: DEFAULT_NEGATIVE_PROMPT,
    seed: '10',

    taskId: null,
    status: 'idle', // idle, queued, running, completed, error
    progress: 0.0,
    stage: 'IDLE · Ready',
    logs: [],
    outputVideoUrl: null,
    outputFilename: null,
    fileSizeMb: null,
    generationStartTime: null,
    pollInterval: null,
    elapsedInterval: null
  };
}

const studioState = {
  slots: [
    createSlot(1, 'Video 1')
  ],
  activeSlotId: 1,
  serverStartTimeMs: Date.now(),
  queuePollInterval: null,
  hasActiveBackendTask: false
};

// Safe DOM Selector Utility
const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

// Helper to get active slot
function getActiveSlot() {
  return studioState.slots.find(s => s.id === studioState.activeSlotId) || studioState.slots[0];
}

// ==========================================
// Initialization on DOM Ready (Instant Zero-Latency Render)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Initializing LongCat-Video-Avatar 1.5 Multi-Slot Studio...');

  // 1. Instant Synchronous State Restoration from localStorage (0.5ms)
  restoreStateFastSync();

  // 2. Immediately render all UI components & Video Tabs (0ms latency!)
  initSlotTabs();
  initDropzones();
  initAudioPlayer();
  initFormControls();
  initActionButtons();
  initModals();
  initGalleryControls();
  initUptimeCounter();

  // 3. Asynchronously restore heavy media blobs from IndexedDB & sync backend queue in background
  restoreMediaFromIndexedDBAndSyncQueue();

  // 4. Check backend server status
  checkBackendHealth();

  // 5. Load existing gallery videos (non-blocking)
  fetchGallery();

  // 6. Start background queue header badge sync
  startQueueSync();
});

// ==========================================
// 1. Multi-Slot Tab Management
// ==========================================
function initSlotTabs() {
  const btnAdd = $('btnAddVideoSlot');
  const btnMonitor = $('btnOpenQueueMonitor');

  if (btnAdd) {
    btnAdd.addEventListener('click', addNewSlot);
  }

  if (btnMonitor) {
    btnMonitor.addEventListener('click', openQueueMonitor);
  }

  renderSlotTabs();
}

let draggedSlotIndex = null;

function renderSlotTabs() {
  const container = $('videoTabsList');
  if (!container) return;

  container.innerHTML = studioState.slots.map((slot, idx) => {
    const isActive = slot.id === studioState.activeSlotId;
    let dotClass = 'idle';
    let statusBadgeHtml = '';

    if (slot.status === 'submitting') {
      dotClass = 'running';
      statusBadgeHtml = `<span class="tab-badge-pill badge-submitting"><span class="mini-pulse-dot"></span>UP ${slot.uploadProgress || 0}%</span>`;
    } else if (slot.status === 'running') {
      dotClass = 'running';
      const pctVal = typeof slot.progress === 'number' ? slot.progress.toFixed(0) : parseFloat(slot.progress || 0).toFixed(0);
      statusBadgeHtml = `<span class="tab-badge-pill badge-running"><span class="mini-pulse-dot"></span>${pctVal}%</span>`;
    } else if (slot.status === 'queued') {
      dotClass = 'queued';
      statusBadgeHtml = `<span class="tab-badge-pill badge-queued">⏳ QUEUE</span>`;
    } else if (slot.status === 'completed') {
      dotClass = 'completed';
      statusBadgeHtml = `<span class="tab-badge-pill badge-ready">✅ READY</span>`;
    } else if (slot.status === 'error') {
      dotClass = 'error';
      statusBadgeHtml = `<span class="tab-badge-pill badge-error">⚠️ ERR</span>`;
    } else {
      statusBadgeHtml = `<span class="tab-badge-pill badge-idle">IDLE</span>`;
    }

    return `
      <div class="video-tab-btn ${isActive ? 'active' : ''} ${slot.status || 'idle'}" 
           draggable="true" 
           data-slot-id="${slot.id}" 
           data-index="${idx}"
           onclick="switchSlot(${slot.id})" 
           title="${slot.title ? escapeHtml(slot.title) : slot.name} · Tap to switch">
        <span class="tab-status-dot ${dotClass}"></span>
        <span class="tab-name-label">🎬 ${escapeHtml(slot.name)}</span>
        ${statusBadgeHtml}
        <span class="tab-close-btn" onclick="removeSlot(event, ${slot.id})" title="Remove Tab">✕</span>
      </div>
    `;
  }).join('');

  attachTabDragAndDropEvents();

  const btnAdd = $('btnAddVideoSlot');
  if (btnAdd) {
    btnAdd.style.display = studioState.slots.length >= 10 ? 'none' : 'inline-flex';
  }

  updateQueueHeaderBadge();
}

function attachTabDragAndDropEvents() {
  const tabs = document.querySelectorAll('.video-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('dragstart', (e) => {
      draggedSlotIndex = parseInt(tab.getAttribute('data-index'));
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', draggedSlotIndex.toString());
      setTimeout(() => tab.classList.add('tab-dragging'), 0);
    });

    tab.addEventListener('dragend', () => {
      tab.classList.remove('tab-dragging');
      document.querySelectorAll('.video-tab-btn').forEach(t => t.classList.remove('tab-drag-over'));
      draggedSlotIndex = null;
    });

    tab.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const targetIndex = parseInt(tab.getAttribute('data-index'));
      if (draggedSlotIndex !== null && draggedSlotIndex !== targetIndex) {
        tab.classList.add('tab-drag-over');
      }
    });

    tab.addEventListener('dragleave', () => {
      tab.classList.remove('tab-drag-over');
    });

    tab.addEventListener('drop', (e) => {
      e.preventDefault();
      tab.classList.remove('tab-drag-over');
      const targetIndex = parseInt(tab.getAttribute('data-index'));
      if (draggedSlotIndex !== null && draggedSlotIndex !== targetIndex) {
        // Re-order slots array smoothly in studioState
        const movedItem = studioState.slots.splice(draggedSlotIndex, 1)[0];
        studioState.slots.splice(targetIndex, 0, movedItem);
        renderSlotTabs();
        saveStudioState();
      }
    });
  });
}

function switchSlot(slotId) {
  if (slotId === studioState.activeSlotId) {
    return;
  }

  // 1. Save current form values to active slot
  saveActiveSlotFromDOM();

  // 2. Set new active slot
  studioState.activeSlotId = slotId;

  // 3. Render tabs
  renderSlotTabs();

  // 4. Populate DOM from new slot
  populateDOMFromActiveSlot();

  saveStudioState();
}

function addNewSlot() {
  if (studioState.slots.length >= 10) {
    alert('Maximum 10 video tabs allowed.');
    return;
  }

  saveActiveSlotFromDOM();

  // Pick lowest missing slot number from 1 to 10
  const existingNumbers = studioState.slots.map(s => {
    const m = (s.name || '').match(/\d+/);
    return m ? parseInt(m[0]) : s.id;
  });
  
  let nextNum = 1;
  while (nextNum <= 10 && existingNumbers.includes(nextNum)) {
    nextNum++;
  }
  if (nextNum > 10) nextNum = studioState.slots.length + 1;

  const existingIds = studioState.slots.map(s => s.id);
  let nextId = nextNum;
  while (existingIds.includes(nextId)) nextId++;

  const slotName = `Video ${nextNum}`;
  const newSlot = createSlot(nextId, slotName);
  studioState.slots.push(newSlot);
  studioState.activeSlotId = nextId;

  renderSlotTabs();
  populateDOMFromActiveSlot();
  saveStudioState();

  appendLog(`[${getTimeString()}] Added new tab: ${slotName}`, 'info');
}

function removeSlot(event, slotId) {
  event.stopPropagation();

  if (studioState.slots.length <= 1) {
    const targetSlot = studioState.slots[0];
    if (targetSlot) {
      if (targetSlot.status === 'running' || targetSlot.status === 'queued') {
        if (!confirm(`Tab "${targetSlot.name}" is currently generating/queued. Reset to clean tab?`)) return;
        stopSlotGeneration(targetSlot);
      }
      studioState.slots = [createSlot(targetSlot.id, targetSlot.name)];
      studioState.activeSlotId = targetSlot.id;
      renderSlotTabs();
      populateDOMFromActiveSlot();
      saveStudioState();
    }
    return;
  }

  const targetSlot = studioState.slots.find(s => s.id === slotId);
  if (!targetSlot) return;

  if (targetSlot.status === 'running' || targetSlot.status === 'queued') {
    if (!confirm(`Tab "${targetSlot.name}" is currently generating or queued. Are you sure you want to remove it?`)) {
      return;
    }
    stopSlotGeneration(targetSlot);
  }

  studioState.slots = studioState.slots.filter(s => s.id !== slotId);
  if (studioState.activeSlotId === slotId) {
    studioState.activeSlotId = studioState.slots[0].id;
  }

  renderSlotTabs();
  populateDOMFromActiveSlot();
  saveStudioState();
}

function saveActiveSlotFromDOM() {
  const slot = getActiveSlot();
  if (!slot) return;

  const titleInput = $('videoTitleInput');
  if (titleInput) slot.title = titleInput.value.trim();

  const promptText = $('motionPromptText');
  if (promptText) slot.prompt = promptText.value;

  const negText = $('negativePromptText');
  if (negText) slot.negativePrompt = negText.value;

  const seedInput = $('seedInput');
  if (seedInput) slot.seed = seedInput.value;

  const checkedNeural = document.querySelector('input[name="neuralDiffusion"]:checked');
  if (checkedNeural) {
    slot.selectedResolution = checkedNeural.value;
  } else if (!slot.selectedResolution || slot.selectedResolution === 'auto') {
    slot.selectedResolution = '500p';
  }

  const checkedFramesPill = document.querySelector('input[name="numFrames"]:checked');
  if (checkedFramesPill) slot.numFrames = parseInt(checkedFramesPill.value) || 205;
  slot.generationMode = 'anchor_seamless';

  const genderSelect = $('genderSelect');
  if (genderSelect && (genderSelect.value === 'male' || genderSelect.value === 'female')) {
    slot.gender = genderSelect.value;
    try { localStorage.setItem(`longcat_slot_${slot.id}_gender`, slot.gender); } catch (e) {}
  }

  const presetSelect = $('presetSelect');
  if (presetSelect) slot.selectedPreset = presetSelect.value;

  const stepsSelect = $('stepsSelect');
  if (stepsSelect) slot.selectedSteps = parseInt(stepsSelect.value) || 3;

  const boosterSelect = $('stepBoosterSelect');
  if (boosterSelect) slot.stepBooster = boosterSelect.value;

  const lengthSelect = $('lengthModeSelect');
  if (lengthSelect) slot.lengthMode = lengthSelect.value;
}

function populateDOMFromActiveSlot() {
  const slot = getActiveSlot();
  if (!slot) return;

  // 0. Populate Video Title
  const titleInput = $('videoTitleInput');
  if (titleInput) titleInput.value = slot.title || '';

  // 1. Populate Reference Photo
  const hasImage = Boolean(slot.imageDataUrl || slot.imageUrl || slot.imageAssetId || (slot.imageName && (slot.imageUrl || slot.imageAssetId || slot.imageDataUrl)));
  if (hasImage) {
    renderImageUI(slot);
  } else {
    clearImageUI(false);
  }

  // 2. Populate Audio
  const hasAudio = Boolean(slot.audioDataUrl || slot.audioUrl || slot.audioName || slot.audioLibraryFilename || slot.audioAssetId);
  if (hasAudio) {
    renderAudioUI(slot);
  } else {
    clearAudioUI(false);
  }

  // 3. Populate Form Inputs
  const promptText = $('motionPromptText');
  if (promptText) {
    if (!slot.prompt || !slot.prompt.startsWith('Use the uploaded image exactly as the reference')) {
      slot.prompt = (slot.gender === 'female') ? FEMALE_POSITIVE_PROMPT : DEFAULT_POSITIVE_PROMPT;
    }
    promptText.value = slot.prompt;
    promptText.placeholder = (slot.gender === 'female') ? FEMALE_POSITIVE_PROMPT : DEFAULT_POSITIVE_PROMPT;
  }

  const negText = $('negativePromptText');
  if (negText) {
    if (!slot.negativePrompt || (!slot.negativePrompt.includes('Aggressive speech, shouting, yelling') && !slot.negativePrompt.includes('Aggressive speech, shouting, wide over-opened mouth'))) {
      slot.negativePrompt = (slot.gender === 'female') ? FEMALE_NEGATIVE_PROMPT : DEFAULT_NEGATIVE_PROMPT;
    }
    negText.value = slot.negativePrompt;
    negText.placeholder = (slot.gender === 'female') ? FEMALE_NEGATIVE_PROMPT : DEFAULT_NEGATIVE_PROMPT;
  }

  const seedInput = $('seedInput');
  if (seedInput) seedInput.value = slot.seed || '10';

  const neuralRadios = document.querySelectorAll('input[name="neuralDiffusion"]');
  if (neuralRadios && neuralRadios.length > 0) {
    const curRes = slot.selectedResolution || '500p';
    neuralRadios.forEach(r => {
      r.checked = (r.value === curRes);
    });
  }

  const framesRadios = document.querySelectorAll('input[name="numFrames"]');
  if (framesRadios && framesRadios.length > 0) {
    const curFrames = slot.numFrames || 205;
    framesRadios.forEach(r => {
      r.checked = (parseInt(r.value) === curFrames);
      const parentLabel = r.closest('.chunk-pill');
      if (parentLabel) {
        if (parseInt(r.value) === curFrames) {
          parentLabel.classList.add('active');
        } else {
          parentLabel.classList.remove('active');
        }
      }
    });
  }

  const genderSelect = $('genderSelect');
  if (genderSelect) {
    if (slot.gender === 'female' || slot.gender === 'male') {
      genderSelect.value = slot.gender;
    } else if (slot.detectedGender === 'female' || slot.detectedGender === 'male') {
      slot.gender = slot.detectedGender;
      genderSelect.value = slot.gender;
    } else {
      let savedSlotGender = '';
      try { savedSlotGender = localStorage.getItem(`longcat_slot_${slot.id}_gender`); } catch (e) {}
      if (savedSlotGender === 'female' || savedSlotGender === 'male') {
        slot.gender = savedSlotGender;
        genderSelect.value = savedSlotGender;
      } else {
        genderSelect.value = slot.gender || '';
      }
    }
  }

  const presetSelect = $('presetSelect');
  if (presetSelect && slot.selectedPreset) presetSelect.value = slot.selectedPreset;

  const stepsSelect = $('stepsSelect');
  if (stepsSelect && slot.selectedSteps) stepsSelect.value = slot.selectedSteps.toString();

  const boosterSelect = $('stepBoosterSelect');
  if (boosterSelect && slot.stepBooster) boosterSelect.value = slot.stepBooster;

  const lengthSelect = $('lengthModeSelect');
  if (lengthSelect && slot.lengthMode) lengthSelect.value = slot.lengthMode;

  // 4. Update Smart Auto-Detect Aspect Card & Gender Badge
  updateSmartAspectCard(slot);

  // 5. Populate Progress & Terminal Logs
  renderProgressUI(slot);
  renderTerminalLogs(slot.logs || []);

  if (slot.outputVideoUrl) {
    loadRenderedVideo(
      slot.outputVideoUrl,
      slot.outputFilename,
      slot.fileSizeMb,
      false,
      slot.name,
      slot.durationFormatted,
      slot.generationTimeFormatted,
      slot.outputVideoUrl720p,
      slot.outputFilename720p,
      slot.fileSize720pMb
    );
  } else {
    resetVideoPlayerUI(slot.name);
  }

  updateSegmentEstimates();
  updateButtonStates(slot);
}

function updateAnchorSeamlessUI(slot = getActiveSlot()) {}

// ==========================================
// 2. Dropzones & File Upload Handlers
// ==========================================
function initDropzones() {
  const imageDropzone = $('imageDropzone');
  const imageInput = $('imageInput');
  const btnChangeImage = $('btnChangeImage');

  if (imageDropzone && imageInput) {
    imageDropzone.addEventListener('click', (e) => {
      if (e.target !== btnChangeImage && !imageDropzone.classList.contains('has-file')) {
        imageInput.click();
      }
    });

    imageInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        processImageFile(e.target.files[0]);
      }
    });

    imageDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      imageDropzone.classList.add('dragover');
    });

    imageDropzone.addEventListener('dragleave', () => {
      imageDropzone.classList.remove('dragover');
    });

    imageDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      imageDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processImageFile(e.dataTransfer.files[0]);
      }
    });

    if (btnChangeImage) {
      btnChangeImage.addEventListener('click', (e) => {
        e.stopPropagation();
        imageInput.click();
      });
    }
  }

  // Audio Dropzone
  const audioDropzone = $('audioDropzone');
  const audioInput = $('audioInput');
  const btnChangeAudio = $('btnChangeAudio');

  if (audioDropzone && audioInput) {
    audioDropzone.addEventListener('click', (e) => {
      if (e.target !== btnChangeAudio && !audioDropzone.classList.contains('has-file')) {
        audioInput.click();
      }
    });

    audioInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        processAudioFile(e.target.files[0]);
      }
    });

    audioDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      audioDropzone.classList.add('dragover');
    });

    audioDropzone.addEventListener('dragleave', () => {
      audioDropzone.classList.remove('dragover');
    });

    audioDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      audioDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processAudioFile(e.dataTransfer.files[0]);
      }
    });

    if (btnChangeAudio) {
      btnChangeAudio.addEventListener('click', (e) => {
        e.stopPropagation();
        audioInput.click();
      });
    }
  }
}

// ==========================================
// Ultra-Fast 16kHz Mono WebAudio Resampler
// Reduces audio payload by ~90% before upload
// ==========================================
async function resampleAudioTo16kMonoWav(file) {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtxClass) return file;
    
    const audioCtx = new AudioCtxClass();
    const decodedBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    
    const targetSampleRate = 16000;
    const targetLength = Math.ceil(decodedBuffer.duration * targetSampleRate);
    const OfflineCtxClass = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    if (!OfflineCtxClass) {
      if (audioCtx.state !== 'closed') audioCtx.close();
      return file;
    }
    
    const offlineCtx = new OfflineCtxClass(1, targetLength, targetSampleRate);
    const source = offlineCtx.createBufferSource();
    source.buffer = decodedBuffer;
    source.connect(offlineCtx.destination);
    source.start(0);
    
    const renderedBuffer = await offlineCtx.startRendering();
    if (audioCtx.state !== 'closed') audioCtx.close();
    
    const pcmData = renderedBuffer.getChannelData(0);
    const wavBlob = encodePCMToWAV(pcmData, targetSampleRate);
    const cleanName = (file.name || 'speech').replace(/\.[^/.]+$/, "") + "_16k.wav";
    return new File([wavBlob], cleanName, { type: 'audio/wav' });
  } catch (err) {
    console.warn("[AUDIO RESAMPLE] WebAudio 16k resample failed, fallback to original file:", err);
    return file;
  }
}

function encodePCMToWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM format = 1
  view.setUint16(22, 1, true); // Mono = 1
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // Byte rate
  view.setUint16(32, 2, true); // Block align
  view.setUint16(34, 16, true); // 16 bits per sample
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([buffer], { type: 'audio/wav' });
}

function triggerBackgroundAssetUpload(slot, type, file) {
  if (!slot || !file) return Promise.resolve(null);
  const formData = new FormData();
  formData.append('file', file, file.name);
  slot[type + 'Uploading'] = true;

  const uploadPromise = fetch('/api/upload_asset', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.success && data.asset_id) {
      slot[type + 'AssetId'] = data.asset_id;
      if (data.url) {
        slot[type + 'Url'] = data.url;
      }
      saveStudioState();
      console.log(`⚡ [BACKGROUND PREUPLOAD] ${type} asset pre-uploaded: ${data.asset_id} (${data.size_mb} MB)`);
    }
    return data;
  })
  .catch(err => {
    console.warn(`[BACKGROUND PREUPLOAD] Background upload error for ${type}:`, err);
    return null;
  })
  .finally(() => {
    slot[type + 'Uploading'] = false;
  });

  slot[type + 'UploadPromise'] = uploadPromise;
  return uploadPromise;
}

function processImageFile(file) {
  if (!file || !file.type.startsWith('image/')) {
    alert('Please upload a valid image file (JPG, PNG, or WEBP)');
    return;
  }

  const targetSlot = getActiveSlot();
  if (!targetSlot) return;

  targetSlot.imageFile = file;
  targetSlot.imageName = file.name;
  targetSlot.imageSizeMb = (file.size / (1024 * 1024)).toFixed(2);
  targetSlot.imageAssetId = null;

  // Immediately start background upload so clicking Generate requires 0s waiting!
  triggerBackgroundAssetUpload(targetSlot, 'image', file);

  const reader = new FileReader();
  reader.onload = (e) => {
    targetSlot.imageDataUrl = e.target.result;
    const img = new Image();
    img.onload = () => {
      targetSlot.imageDimensions = `${img.width}×${img.height}`;

      // Smart Aspect Ratio Detection & Framing
      const aspectRatio = img.width / img.height;
      let detectedRatio = '9:16';
      let ratioTitle = '9:16 Portrait (Reels / Shorts / TikTok)';
      let targetRes = '1080x1920';

      if (aspectRatio > 1.30) {
        detectedRatio = '16:9';
        ratioTitle = '16:9 Landscape (YouTube Full HD)';
        targetRes = '1920x1080';
      } else if (aspectRatio < 0.78) {
        detectedRatio = '9:16';
        ratioTitle = '9:16 Portrait (Reels / Shorts / TikTok)';
        targetRes = '1080x1920';
      } else if (aspectRatio >= 0.85 && aspectRatio <= 1.15) {
        detectedRatio = '1:1';
        ratioTitle = '1:1 Square (Instagram / Post)';
        targetRes = '1024x1024';
      } else {
        detectedRatio = '4:5';
        ratioTitle = '4:5 Portrait Feed';
        targetRes = '1080x1350';
      }

      // Detect Source Quality Level
      let qualityLabel = '';
      if (img.width >= 3840 || img.height >= 3840) {
        qualityLabel = `4K Ultra HD (${img.width}×${img.height})`;
      } else if (img.width >= 2560 || img.height >= 2560) {
        qualityLabel = `2K QHD (${img.width}×${img.height})`;
      } else if (img.width >= 1920 || img.height >= 1920 || parseFloat(targetSlot.imageSizeMb) >= 2.0) {
        qualityLabel = `1080P Full HD (${img.width}×${img.height})`;
      } else if (img.width >= 1280 || img.height >= 1280) {
        qualityLabel = `720P HD (${img.width}×${img.height})`;
      } else {
        qualityLabel = `Standard HD (${img.width}×${img.height})`;
      }

      targetSlot.detectedRatio = detectedRatio;
      targetSlot.detectedResolution = targetRes;
      // Auto-detect gender from uploaded image / filename
      const lowerName = (file.name || '').toLowerCase();
      let detectedGender = 'male';
      if (lowerName.includes('woman') || lowerName.includes('female') || lowerName.includes('girl') || lowerName.includes('lady') || lowerName.includes('she') || lowerName.includes('her') || lowerName.includes('women') || lowerName.includes('miss') || lowerName.includes('mrs') || lowerName.includes('hijab') || lowerName.includes('sister') || lowerName.includes('daughter') || lowerName.includes('mother') || lowerName.includes('aunt') || lowerName.includes('queen') || lowerName.includes('bride')) {
        detectedGender = 'female';
      } else if (lowerName.includes('man') || lowerName.includes('male') || lowerName.includes('boy') || lowerName.includes('guy') || lowerName.includes('he') || lowerName.includes('his') || lowerName.includes('men') || lowerName.includes('mr') || lowerName.includes('sir') || lowerName.includes('gentleman') || lowerName.includes('brother') || lowerName.includes('son') || lowerName.includes('father') || lowerName.includes('uncle') || lowerName.includes('king') || lowerName.includes('groom') || lowerName.includes('beard')) {
        detectedGender = 'male';
      } else {
        // If filename is generic (e.g. photo.jpg, avatar.png), preserve existing slot selection if already set, else default to male
        detectedGender = (targetSlot.gender === 'female' || targetSlot.gender === 'male') ? targetSlot.gender : 'male';
      }

      targetSlot.detectedGender = detectedGender;
      targetSlot.gender = detectedGender;
      try { localStorage.setItem(`longcat_slot_${targetSlot.id}_gender`, detectedGender); } catch (e) {}
      if (detectedGender === 'female') {
        targetSlot.prompt = FEMALE_POSITIVE_PROMPT;
        targetSlot.negativePrompt = FEMALE_NEGATIVE_PROMPT;
      } else if (detectedGender === 'male') {
        targetSlot.prompt = DEFAULT_POSITIVE_PROMPT;
        targetSlot.negativePrompt = DEFAULT_NEGATIVE_PROMPT;
      }
      targetSlot.selectedRatio = 'auto';
      targetSlot.selectedResolution = '500p';

      const currentActive = getActiveSlot();
      if (currentActive && currentActive.id === targetSlot.id) {
        const resSelect = $('resolutionSelect');
        if (resSelect) {
          resSelect.value = 'auto';
          const autoOpt = resSelect.querySelector('option[value="auto"]');
          if (autoOpt) {
            autoOpt.textContent = `⚡ Auto (Native Source HD Master • Matched ${detectedRatio} 1080P • Default)`;
          }
        }
        const genderSelect = $('genderSelect');
        if (genderSelect) {
          genderSelect.value = detectedGender;
        }
        const promptText = $('motionPromptText');
        if (promptText) promptText.value = targetSlot.prompt;
        const negText = $('negativePromptText');
        if (negText) negText.value = targetSlot.negativePrompt;

        updateSmartAspectCard(targetSlot);
        updateGenderUI(targetSlot);
        renderImageUI(targetSlot);
        applyVideoPlayerAspect($('mainVideoPlayer'), detectedRatio);
      }

      appendLog(`[${getTimeString()}] ✨ Auto-detected ${ratioTitle} & Gender: ${detectedGender.toUpperCase()} for ${targetSlot.name}`, 'info');

      saveStudioState();
    };
    img.src = targetSlot.imageDataUrl;
  };
  reader.readAsDataURL(file);
}

function updateSmartAspectCard(slot = getActiveSlot()) {
  const card = $('smartAspectCard');
  const icon = $('smartAspectIcon');
  const iconText = $('smartAspectIconText');
  const title = $('smartAspectTitle');
  const sub = $('smartAspectSub');
  const targetBadge = $('smartTargetBadge');

  if (!card) return;

  if (slot && (slot.imageDataUrl || slot.imageUrl || slot.imageName) && slot.detectedRatio) {
    const ratio = slot.detectedRatio;
    const res = slot.detectedResolution || '1920x1080';
    const quality = slot.detectedQualityLabel || 'HD Quality';
    const dim = slot.imageDimensions || '';

    if (icon) {
      icon.className = `smart-aspect-icon ratio-${ratio.replace(':', '-')}`;
    }
    if (iconText) {
      iconText.textContent = ratio.toUpperCase();
    }
    if (title) {
      let friendlyTitle = '16:9 Landscape (YouTube Full HD)';
      if (ratio === '9:16') friendlyTitle = '9:16 Portrait (Reels / Shorts)';
      else if (ratio === '1:1') friendlyTitle = '1:1 Square (Instagram Post)';
      else if (ratio === '4:5') friendlyTitle = '4:5 Feed Portrait';
      title.innerHTML = `✨ <strong>Auto-Detected:</strong> ${friendlyTitle}`;
    }
    if (sub) {
      sub.innerHTML = `Source: <strong>${dim} (${quality} · ${slot.imageSizeMb || '1.0'} MB)</strong> → Target: <strong>${res} Studio Master</strong>`;
    }
    if (targetBadge) {
      targetBadge.textContent = `${ratio} Master HD`;
    }
    card.classList.add('active');
  } else {
    if (icon) icon.className = 'smart-aspect-icon ratio-auto';
    if (iconText) iconText.textContent = '⚡ AUTO';
    if (title) title.textContent = '⚡ Auto-Detect Ratio & Framing';
    if (sub) sub.textContent = 'Drop or select an image — Automatically adapts to 16:9 Landscape, 9:16 Portrait, or 1:1 Square';
    if (targetBadge) targetBadge.textContent = 'Studio Master HD';
  }

  updateGenderUI(slot);
  applyVideoPlayerAspect($('mainVideoPlayer'), (slot && slot.detectedRatio) ? slot.detectedRatio : '9:16');
}

function updateGenderUI(slot = getActiveSlot()) {
  const badge = $('genderAutoBadge');
  const genderSelect = $('genderSelect');
  if (!badge) return;
  const g = (slot && (slot.gender === 'female' || slot.gender === 'male')) ? slot.gender : (genderSelect && (genderSelect.value === 'female' || genderSelect.value === 'male') ? genderSelect.value : '');
  if (g === 'female') {
    badge.textContent = '✨ 👩 Female: Natural Respiration & Bust Movement Dynamics Active';
    badge.style.background = 'rgba(236, 72, 153, 0.35)';
    badge.style.color = '#ffffff';
    badge.style.fontWeight = '800';
    badge.style.border = '1px solid rgba(236, 72, 153, 0.7)';
  } else if (g === 'male') {
    badge.textContent = '✨ 👨 Male: Standard Masculine Posture Active';
    badge.style.background = 'rgba(16, 185, 129, 0.35)';
    badge.style.color = '#ffffff';
    badge.style.fontWeight = '800';
    badge.style.border = '1px solid rgba(16, 185, 129, 0.7)';
  } else {
    badge.textContent = '✨ Ready to Auto-Scan';
    badge.style.background = 'rgba(255, 255, 255, 0.12)';
    badge.style.color = '#ffffff';
    badge.style.fontWeight = '800';
    badge.style.border = '1px solid rgba(255, 255, 255, 0.25)';
  }
}

function truncateFileName(name, maxWords = 5) {
  if (!name) return '';
  const lastDot = name.lastIndexOf('.');
  const ext = lastDot !== -1 ? name.substring(lastDot) : '';
  const base = lastDot !== -1 ? name.substring(0, lastDot) : name;

  const words = base.split(/[\s_\-]+/).filter(Boolean);
  if (words.length > maxWords) {
    return words.slice(0, maxWords).join('_') + '...' + ext;
  }
  if (base.length > 28) {
    return base.substring(0, 25) + '...' + ext;
  }
  return name;
}

function renderImageUI(slot = getActiveSlot()) {
  if (!slot) return;
  const emptyState = $('imageEmptyState');
  const filledState = $('imageFilledState');
  const previewImg = $('imagePreviewImg');
  const fileNameEl = $('imageFileName');
  const fileMetaEl = $('imageFileMeta');
  const dropzone = $('imageDropzone');

  let imgSrc = slot.imageDataUrl || slot.imageUrl;
  if (!imgSrc && slot.imageAssetId) {
    imgSrc = `/uploads/preupload/${slot.imageAssetId}.jpeg`;
    slot.imageUrl = imgSrc;
  }

  if (previewImg && imgSrc) {
    if (previewImg.src !== imgSrc && !previewImg.src.endsWith(imgSrc)) {
      previewImg.src = imgSrc;
    }
    if (fileNameEl) {
      fileNameEl.textContent = truncateFileName(slot.imageName || 'portrait.jpg', 5);
      fileNameEl.title = slot.imageName || 'portrait.jpg';
    }
    if (fileMetaEl) fileMetaEl.textContent = `${slot.imageDimensions || '768×1280'} · ${slot.imageSizeMb || '0.65'} MB`;

    if (emptyState) emptyState.classList.add('hidden');
    if (filledState) filledState.classList.remove('hidden');
    if (dropzone) dropzone.classList.add('has-file');

    updateSmartAspectCard(slot);
    updateGenderUI(slot);

    // Background rehydrate imageDataUrl from imageUrl if needed
    if (slot.imageUrl && !slot.imageDataUrl && !slot._rehydrating) {
      slot._rehydrating = true;
      fetch(slot.imageUrl)
        .then(res => res.ok ? res.blob() : null)
        .then(blob => {
          if (blob) {
            slot.imageFile = blob;
            const r = new FileReader();
            r.onload = (e) => { slot.imageDataUrl = e.target.result; };
            r.readAsDataURL(blob);
          }
        })
        .catch(() => {})
        .finally(() => { slot._rehydrating = false; });
    }

    appendLog(`[${getTimeString()}] Face image loaded for ${slot.name}: ${slot.imageName || 'portrait.jpg'}`, 'info');
  } else if (slot.imageName) {
    if (fileNameEl) {
      fileNameEl.textContent = truncateFileName(slot.imageName, 5);
      fileNameEl.title = slot.imageName;
    }
    if (fileMetaEl && slot.imageDimensions) {
      fileMetaEl.textContent = `${slot.imageDimensions} · ${slot.imageSizeMb || '0.65'} MB`;
    }
    if (emptyState) emptyState.classList.add('hidden');
    if (filledState) filledState.classList.remove('hidden');
    if (dropzone) dropzone.classList.add('has-file');
    updateSmartAspectCard(slot);
    updateGenderUI(slot);
  }
}

function clearImageUI(clearData = true) {
  const slot = getActiveSlot();
  if (clearData && slot) {
    slot.imageFile = null;
    slot.imageDataUrl = null;
    slot.imageName = null;
    slot.imageDimensions = null;
    slot.imageSizeMb = null;
    slot.imageUrl = null;
    slot.imageAssetId = null;
    slot.detectedRatio = null;
    slot.detectedResolution = null;
    slot.detectedQualityLabel = null;
    slot.detectedRatioTitle = null;
    slot.detectedGender = '';
    slot.gender = '';
    try { localStorage.removeItem(`longcat_slot_${slot.id}_gender`); } catch (e) {}
    const genderSelect = $('genderSelect');
    if (genderSelect) genderSelect.value = '';
    updateGenderUI(slot);
    saveStudioState();
  }

  const imageInput = $('imageInput');
  if (imageInput) imageInput.value = '';

  const emptyState = $('imageEmptyState');
  const filledState = $('imageFilledState');
  const previewImg = $('imagePreviewImg');
  const badge = $('imageAutoDetectBadge');

  if (previewImg) previewImg.src = '';
  if (filledState) filledState.classList.add('hidden');
  if (emptyState) emptyState.classList.remove('hidden');
  if (badge) badge.classList.add('hidden');

  updateSmartAspectCard(slot);

  const dropzone = $('imageDropzone');
  if (dropzone) dropzone.classList.remove('has-file');
}

async function processAudioFile(file) {
  if (!file) return;

  const targetSlot = getActiveSlot();
  if (!targetSlot) return;

  targetSlot.audioFile = file;
  targetSlot.audioName = file.name;
  targetSlot.audioSizeMb = (file.size / (1024 * 1024)).toFixed(2);
  targetSlot.audioAssetId = null;

  // 1. Instant zero-RAM audio duration measurement using Object URL
  const audioBlobUrl = URL.createObjectURL(file);
  const tempAudio = new Audio(audioBlobUrl);
  tempAudio.onloadedmetadata = () => {
    targetSlot.audioDuration = tempAudio.duration || 0;
    const currentActive = getActiveSlot();
    if (currentActive && currentActive.id === targetSlot.id) {
      renderAudioUI(targetSlot);
      updateSegmentEstimates();
    }
    saveStudioState();
    URL.revokeObjectURL(audioBlobUrl);
  };

  // 2. Ultra-Fast Client-side 16kHz Mono Resampling & Instant Background Pre-Upload
  try {
    const clean16kFile = await resampleAudioTo16kMonoWav(file);
    targetSlot.audioFile = clean16kFile;
    targetSlot.audioSizeMb = (clean16kFile.size / (1024 * 1024)).toFixed(2);
    triggerBackgroundAssetUpload(targetSlot, 'audio', clean16kFile);
  } catch (err) {
    console.warn("Client 16k resample failed, using original file:", err);
    targetSlot.audioFile = file;
    triggerBackgroundAssetUpload(targetSlot, 'audio', file);
  }

  // 3. Keep lightweight dataUrl for state caching
  const reader = new FileReader();
  reader.onload = (e) => {
    targetSlot.audioDataUrl = e.target.result;
    saveStudioState();
  };
  reader.readAsDataURL(targetSlot.audioFile || file);
}

function renderAudioUI(slot = getActiveSlot()) {
  if (!slot) return;
  const emptyState = $('audioEmptyState');
  const filledState = $('audioFilledState');
  const fileNameEl = $('audioFileName');
  const fileMetaEl = $('audioFileMeta');
  const durationEl = $('audioDurationTime');
  const currTimeEl = $('audioCurrentTime');
  const slider = $('audioSeekSlider');
  const dropzone = $('audioDropzone');
  const audioEl = $('audioPlayerElement');
  const playBtn = $('audioPlayPauseBtn');

  if (fileNameEl) {
    fileNameEl.textContent = truncateFileName(slot.audioName || 'speech.wav', 5);
    fileNameEl.title = slot.audioName || 'speech.wav';
  }
  if (fileMetaEl) fileMetaEl.textContent = `${formatTime(slot.audioDuration)} · ${slot.audioSizeMb || '2.5'} MB`;
  if (durationEl) durationEl.textContent = formatTime(slot.audioDuration);
  if (currTimeEl) currTimeEl.textContent = '0:00';
  if (slider) slider.value = 0;

  if (audioEl) {
    audioEl.pause();
    if (!slot.audioUrl && slot.audioLibraryFilename) {
      slot.audioUrl = `/audio_library/${encodeURIComponent(slot.audioLibraryFilename)}`;
    }
    if (slot.audioDataUrl) {
      if (audioEl.src !== slot.audioDataUrl) {
        audioEl.src = slot.audioDataUrl;
      }
    } else if (slot.audioUrl) {
      const fullUrl = slot.audioUrl.startsWith('http') ? slot.audioUrl : (window.location.origin + slot.audioUrl);
      if (audioEl.src !== fullUrl) {
        audioEl.src = fullUrl;
      }
    } else if (slot.audioFile) {
      audioEl.src = URL.createObjectURL(slot.audioFile);
    } else {
      audioEl.src = '';
    }
    audioEl.currentTime = 0;
  }

  if (playBtn) {
    const playIcon = playBtn.querySelector('.play-icon');
    const pauseIcon = playBtn.querySelector('.pause-icon');
    if (playIcon) playIcon.classList.remove('hidden');
    if (pauseIcon) pauseIcon.classList.add('hidden');
  }

  if (emptyState) emptyState.classList.add('hidden');
  if (filledState) filledState.classList.remove('hidden');
  if (dropzone) dropzone.classList.add('has-file');

  appendLog(`[${getTimeString()}] Audio loaded for ${slot.name}: ${slot.audioName} (${formatTime(slot.audioDuration)})`, 'info');
}

function clearAudioUI(clearData = true) {
  const audioEl = $('audioPlayerElement');
  if (audioEl) {
    audioEl.pause();
    audioEl.src = '';
  }

  const slot = getActiveSlot();
  if (clearData && slot) {
    slot.audioFile = null;
    slot.audioDataUrl = null;
    slot.audioName = null;
    slot.audioDuration = 0;
    slot.audioSizeMb = null;
    slot.audioUrl = null;
    slot.audioAssetId = null;
    slot.audioLibraryFilename = null;
    saveStudioState();
  }

  const audioInput = $('audioInput');
  if (audioInput) audioInput.value = '';

  const emptyState = $('audioEmptyState');
  const filledState = $('audioFilledState');
  const dropzone = $('audioDropzone');

  if (emptyState) emptyState.classList.remove('hidden');
  if (filledState) filledState.classList.add('hidden');
  if (dropzone) dropzone.classList.remove('has-file');

  updateSegmentEstimates();
}

// ==========================================
// 3. Audio Player Controls
// ==========================================
function initAudioPlayer() {
  const audioEl = $('audioPlayerElement');
  const playBtn = $('audioPlayPauseBtn');
  const slider = $('audioSeekSlider');
  const currTime = $('audioCurrentTime');

  if (!audioEl || !playBtn) return;

  playBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();

    const slot = getActiveSlot();
    if (!audioEl.src && slot) {
      if (slot.audioDataUrl) {
        audioEl.src = slot.audioDataUrl;
      } else if (slot.audioFile) {
        audioEl.src = URL.createObjectURL(slot.audioFile);
      }
    }

    if (!audioEl.src) {
      console.warn('No audio src available to play');
      return;
    }

    const playIcon = playBtn.querySelector('.play-icon');
    const pauseIcon = playBtn.querySelector('.pause-icon');

    if (audioEl.paused) {
      const playPromise = audioEl.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          if (playIcon) playIcon.classList.add('hidden');
          if (pauseIcon) pauseIcon.classList.remove('hidden');
        }).catch(err => {
          console.warn('Audio play error:', err);
        });
      }
    } else {
      audioEl.pause();
      if (playIcon) playIcon.classList.remove('hidden');
      if (pauseIcon) pauseIcon.classList.add('hidden');
    }
  });

  audioEl.addEventListener('timeupdate', () => {
    if (!audioEl.duration) return;
    const pct = (audioEl.currentTime / audioEl.duration) * 100;
    if (slider) slider.value = pct;
    if (currTime) currTime.textContent = formatTime(audioEl.currentTime);
  });

  audioEl.addEventListener('ended', () => {
    const playIcon = playBtn.querySelector('.play-icon');
    const pauseIcon = playBtn.querySelector('.pause-icon');
    if (playIcon) playIcon.classList.remove('hidden');
    if (pauseIcon) pauseIcon.classList.add('hidden');
    if (slider) slider.value = 0;
    if (currTime) currTime.textContent = '0:00';
    audioEl.currentTime = 0;
  });

  if (slider) {
    slider.addEventListener('input', () => {
      if (!audioEl.duration) return;
      audioEl.currentTime = (slider.value / 100) * audioEl.duration;
    });
  }
}

// ==========================================
// 4. Form Controls & Aspect Ratio Handlers
// ==========================================
function initFormControls() {
  const neuralRadios = document.querySelectorAll('input[name="neuralDiffusion"]');
  neuralRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      const slot = getActiveSlot();
      if (slot) {
        slot.selectedResolution = radio.value;
        saveStudioState();
      }
    });
  });



  const framesRadios = document.querySelectorAll('input[name="numFrames"]');
  framesRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      const slot = getActiveSlot();
      if (slot) {
        slot.numFrames = parseInt(radio.value) || 205;
        slot.generationMode = 'anchor_seamless';
        saveStudioState();
      }
      framesRadios.forEach(r => {
        const parentLabel = r.closest('.chunk-pill');
        if (parentLabel) {
          if (r.checked) parentLabel.classList.add('active');
          else parentLabel.classList.remove('active');
        }
      });
    });
  });

  const resSelect = $('resolutionSelect');

  if (resSelect) {
    resSelect.addEventListener('change', () => {
      const slot = getActiveSlot();
      slot.selectedResolution = resSelect.value;
      if (resSelect.value === '1920x1080' || resSelect.value === '1280x768') {
        slot.selectedRatio = '16:9';
      } else if (resSelect.value === '1080x1920' || resSelect.value === '768x1280') {
        slot.selectedRatio = '9:16';
      } else if (resSelect.value === '1024x1024' || resSelect.value === '768x768') {
        slot.selectedRatio = '1:1';
      } else {
        slot.selectedRatio = 'auto';
      }
      updateSmartAspectCard(slot);
      saveStudioState();
    });
  }

  const genderSelect = $('genderSelect');
  if (genderSelect) {
    genderSelect.addEventListener('change', () => {
      const slot = getActiveSlot();
      if (slot) {
        slot.gender = genderSelect.value;
        try { localStorage.setItem(`longcat_slot_${slot.id}_gender`, slot.gender); } catch (e) {}
        if (slot.gender === 'female') {
          slot.prompt = FEMALE_POSITIVE_PROMPT;
          slot.negativePrompt = FEMALE_NEGATIVE_PROMPT;
          const promptText = $('motionPromptText');
          if (promptText) promptText.value = FEMALE_POSITIVE_PROMPT;
          const negText = $('negativePromptText');
          if (negText) negText.value = FEMALE_NEGATIVE_PROMPT;
        } else if (slot.gender === 'male') {
          slot.prompt = DEFAULT_POSITIVE_PROMPT;
          slot.negativePrompt = DEFAULT_NEGATIVE_PROMPT;
          const promptText = $('motionPromptText');
          if (promptText) promptText.value = DEFAULT_POSITIVE_PROMPT;
          const negText = $('negativePromptText');
          if (negText) negText.value = DEFAULT_NEGATIVE_PROMPT;
        }
      }
      updateGenderUI(slot);
      saveStudioState();
    });
  }

  const presetSelect = $('presetSelect');
  if (presetSelect) {
    presetSelect.addEventListener('change', () => {
      const slot = getActiveSlot();
      slot.selectedPreset = presetSelect.value;
      saveStudioState();
    });
  }

  const stepsSelect = $('stepsSelect');
  if (stepsSelect) {
    stepsSelect.addEventListener('change', () => {
      const slot = getActiveSlot();
      slot.selectedSteps = parseInt(stepsSelect.value) || 3;
      saveStudioState();
    });
  }

  const boosterSelect = $('stepBoosterSelect');
  if (boosterSelect) {
    boosterSelect.addEventListener('change', () => {
      const slot = getActiveSlot();
      slot.stepBooster = boosterSelect.value;
      saveStudioState();
    });
  }

  const lengthModeSelect = $('lengthModeSelect');
  if (lengthModeSelect) {
    lengthModeSelect.addEventListener('change', () => {
      const slot = getActiveSlot();
      slot.lengthMode = lengthModeSelect.value;
      updateSegmentEstimates();
      saveStudioState();
    });
  }

  const titleInput = $('videoTitleInput');
  if (titleInput) {
    titleInput.addEventListener('input', () => {
      const slot = getActiveSlot();
      slot.title = titleInput.value;
      saveStudioState();
    });
  }

  const promptText = $('motionPromptText');
  if (promptText) {
    promptText.addEventListener('input', () => {
      const slot = getActiveSlot();
      slot.prompt = promptText.value;
      saveStudioState();
    });
  }

  const negText = $('negativePromptText');
  if (negText) {
    negText.addEventListener('input', () => {
      const slot = getActiveSlot();
      slot.negativePrompt = negText.value;
      saveStudioState();
    });
  }

  const seedInput = $('seedInput');
  if (seedInput) {
    seedInput.addEventListener('input', () => {
      const slot = getActiveSlot();
      slot.seed = seedInput.value;
      saveStudioState();
    });
  }

  const btnRandomSeed = $('btnRandomSeed');
  if (btnRandomSeed && seedInput) {
    btnRandomSeed.addEventListener('click', () => {
      seedInput.value = Math.floor(Math.random() * 999999);
      const slot = getActiveSlot();
      slot.seed = seedInput.value;
      saveStudioState();
    });
  }

  // 🗑️ Delete All (Reset) Handler
  const btnDeleteAll = $('btnDeleteAllSlots');
  if (btnDeleteAll) {
    btnDeleteAll.addEventListener('click', async () => {
      const runningCount = studioState.slots.filter(s => s.status === 'running').length;
      if (runningCount > 0) {
        if (!confirm('Some videos are currently generating. Are you sure you want to reset all tabs and inputs? (Running tasks on GPU will continue in background)')) return;
      } else {
        if (!confirm('Are you sure you want to delete and reset all video tabs, photos, and audio files back to fresh empty state?')) return;
      }

      studioState.slots = [createSlot(1, 'Video 1')];
      studioState.activeSlotId = 1;
      clearImageUI(false);
      clearAudioUI(false);
      renderSlotTabs();
      populateDOMFromActiveSlot();
      await saveStudioState();
      appendLog(`[${getTimeString()}] 🗑️ All video tabs, uploaded media, and forms have been cleared.`, 'info');
    });
  }

  // 🚀 Generate All Batch Handler
  const btnGenerateAll = $('btnGenerateAllSlots');
  if (btnGenerateAll) {
    btnGenerateAll.addEventListener('click', async () => {
      saveActiveSlotFromDOM();

      const readySlots = studioState.slots.filter(s => (s.imageFile || s.imageDataUrl) && (s.audioFile || s.audioDataUrl) && s.status !== 'running' && s.status !== 'completed');

      if (readySlots.length === 0) {
        alert('No ready video tabs found! Please upload a portrait photo and speech audio in at least one video tab before clicking Generate All.');
        return;
      }

      readySlots.forEach(s => {
        if (s.status === 'idle' || s.status === 'error') {
          s.status = 'queued';
          s.stage = 'In GPU Queue...';
        }
      });

      renderSlotTabs();
      await saveStudioState();
      appendLog(`[${getTimeString()}] 🚀 Batch "Generate All" initiated for ${readySlots.length} video(s)! Discarding idle state & launching auto-pipeline...`, 'success');

      await processNextQueuedSlot();
    });
  }
}

function updateSegmentEstimates() {
  const slot = getActiveSlot();
  const duration = slot ? slot.audioDuration : 10.0;
  const lengthMode = slot ? slot.lengthMode : 'auto';
  let numSegments = 1;

  if (lengthMode === 'auto') {
    if (duration <= 5.0) {
      numSegments = 1;
    } else {
      const rem = duration - 5.0;
      numSegments = 1 + Math.ceil(rem / 4.48);
    }
  } else {
    numSegments = parseInt(lengthMode) || 1;
  }

  const segBadge = $('segmentCountDisplay');
  if (segBadge) {
    segBadge.textContent = `Est. Segments: ${lengthMode === 'auto' ? 'Auto' : lengthMode} (${numSegments} Segment${numSegments > 1 ? 's' : ''})`;
  }

  const metricTotal = $('metricTotal');
  if (metricTotal) {
    const totalSec = numSegments === 1 ? Math.min(duration, 5.0) : 5.0 + (numSegments - 1) * 4.48;
    metricTotal.textContent = formatTime(totalSec);
  }
}

// ==========================================
// 5. Action Buttons (Generate, Stop, Clear)
// ==========================================
function initActionButtons() {
  const btnGenerate = $('btnGenerateAvatar');
  const btnStop = $('btnStopGeneration');
  const btnRefresh = $('btnRefreshStatus');
  const btnClearAll = $('btnClearAllFields');
  const btnClearLog = $('btnClearLog');

  if (btnGenerate) {
    btnGenerate.addEventListener('click', startActiveSlotGeneration);
  }

  if (btnStop) {
    btnStop.addEventListener('click', () => {
      const slot = getActiveSlot();
      if (confirm(`Are you sure you want to stop generation for ${slot.name}?`)) {
        stopSlotGeneration(slot);
      }
    });
  }

  // Initialize Floating Action Dock
  initFloatingDockDragAndActions();

  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      checkBackendHealth();
      fetchGallery();
      fetchQueueStatus();
      appendLog(`[${getTimeString()}] Status, queue, and gallery refreshed.`, 'system');
    });
  }

  if (btnClearAll) {
    btnClearAll.addEventListener('click', () => {
      if (confirm('Clear all inputs and reset current tab?')) {
        clearImageUI(true);
        clearAudioUI(true);
        const slot = getActiveSlot();
        slot.prompt = (slot.gender === 'female') ? FEMALE_POSITIVE_PROMPT : DEFAULT_POSITIVE_PROMPT;
        slot.negativePrompt = (slot.gender === 'female') ? FEMALE_NEGATIVE_PROMPT : DEFAULT_NEGATIVE_PROMPT;
        slot.seed = '10';
        populateDOMFromActiveSlot();
        appendLog(`[${getTimeString()}] Form inputs cleared for ${slot.name}.`, 'muted');
      }
    });
  }

  const btnCopyLog = $('btnCopyLog');
  if (btnCopyLog) {
    btnCopyLog.addEventListener('click', async () => {
      const logBody = $('terminalLogBody');
      if (!logBody) return;

      const lines = Array.from(logBody.querySelectorAll('.log-line'))
        .map(el => el.innerText.trim())
        .filter(Boolean)
        .join('\n');

      if (!lines) {
        alert('No log text to copy.');
        return;
      }

      try {
        await navigator.clipboard.writeText(lines);
        const copyText = $('copyLogText');
        btnCopyLog.classList.add('copied');
        if (copyText) copyText.textContent = 'Copied!';
        setTimeout(() => {
          btnCopyLog.classList.remove('copied');
          if (copyText) copyText.textContent = 'Copy';
        }, 2000);
      } catch (err) {
        const textarea = document.createElement('textarea');
        textarea.value = lines;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        const copyText = $('copyLogText');
        btnCopyLog.classList.add('copied');
        if (copyText) copyText.textContent = 'Copied!';
        setTimeout(() => {
          btnCopyLog.classList.remove('copied');
          if (copyText) copyText.textContent = 'Copy';
        }, 2000);
      }
    });
  }

  if (btnClearLog) {
    btnClearLog.addEventListener('click', () => {
      const slot = getActiveSlot();
      slot.logs = [];
      const logBody = $('terminalLogBody');
      if (logBody) {
        logBody.innerHTML = `<div class="log-line system"><span class="log-ts">[${getTimeString()}]</span> Terminal cleared.</div>`;
      }
    });
  }
}

// ==========================================
// ==========================================
async function uploadAndGenerateSlot(formData, onProgress, maxRetries = 2) {
  let lastError = null;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/generate');
        // Uncapped upload timeout: allows massive 24+ minute audio voiceovers (200MB-1GB+) to upload completely without premature cutoff
        xhr.timeout = 0;

        let lastTime = Date.now();
        let lastLoaded = 0;
        let currentSpeedStr = '';
        let currentEtaStr = '';

        if (xhr.upload && onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable && e.total > 0) {
              const now = Date.now();
              const timeDiff = (now - lastTime) / 1000;

              if (timeDiff >= 0.5) {
                const bytesDiff = e.loaded - lastLoaded;
                const speedMBps = (bytesDiff / (1024 * 1024)) / timeDiff;
                if (speedMBps > 0.01) {
                  currentSpeedStr = `${speedMBps.toFixed(1)} MB/s`;
                  const remainingBytes = e.total - e.loaded;
                  const remainingSec = Math.max(1, Math.round((remainingBytes / (1024 * 1024)) / speedMBps));
                  currentEtaStr = remainingSec >= 60 
                    ? `ETA ~${Math.floor(remainingSec / 60)}m ${remainingSec % 60}s` 
                    : `ETA ~${remainingSec}s`;
                }
                lastTime = now;
                lastLoaded = e.loaded;
              }

              const pct = Math.min(99, Math.round((e.loaded / e.total) * 100));
              const loadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
              const totalMB = (e.total / (1024 * 1024)).toFixed(1);
              onProgress(pct, loadedMB, totalMB, currentSpeedStr, currentEtaStr);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              resolve(data);
            } catch (err) {
              reject(new Error('Invalid JSON response from server'));
            }
          } else {
            try {
              const errData = JSON.parse(xhr.responseText);
              reject(new Error(errData.error || `HTTP Error ${xhr.status}`));
            } catch (e) {
              reject(new Error(`HTTP Error ${xhr.status}: ${xhr.statusText}`));
            }
          }
        };

        xhr.ontimeout = () => reject(new Error('Upload timed out. Server or tunnel may be busy.'));
        xhr.onerror = () => reject(new Error('Network upload connection failed. Check connection or tunnel.'));
        xhr.onabort = () => reject(new Error('Upload was cancelled'));
        xhr.send(formData);
      });
    } catch (err) {
      lastError = err;
      if (attempt < maxRetries) {
        console.warn(`[Upload] Attempt ${attempt} failed: ${err.message}. Retrying in 2s...`);
        if (onProgress) onProgress(0, '0', '0', '', '');
        await new Promise(r => setTimeout(r, 2000));
      }
    }
  }
  throw lastError;
}

async function startActiveSlotGeneration() {
  const slot = getActiveSlot();

  const hasDirectImage = Boolean(slot.imageFile || slot.imageDataUrl || slot.imageUrl || slot.imageAssetId);

  if (!hasDirectImage) {
    alert('Please upload a Face / Portrait Image first!');
    const dropzone = $('imageDropzone');
    if (dropzone) {
      dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' });
      dropzone.style.borderColor = '#ef4444';
      setTimeout(() => { dropzone.style.borderColor = ''; }, 1500);
    }
    return;
  }

  const hasDirectAudio = Boolean(slot.audioLibraryFilename || slot.audioFile || slot.audioDataUrl || slot.audioUrl || slot.audioAssetId);
  if (!hasDirectAudio) {
    alert('Please upload a Speech Audio Voiceover file first!');
    const dropzone = $('audioDropzone');
    if (dropzone) {
      dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' });
      dropzone.style.borderColor = '#ef4444';
      setTimeout(() => { dropzone.style.borderColor = ''; }, 1500);
    }
    return;
  }

  // 1. INSTANT ZERO-LATENCY FEEDBACK (0ms):
  slot.status = 'submitting';
  slot.uploadProgress = 0;
  slot.uploadProgressText = 'Preparing & Uploading Voiceover...';
  slot.stage = 'Uploading Audio & Photo Assets to Server...';
  slot.progress = 0.0;
  slot.generationStartTime = Date.now();

  updateButtonStates(slot);
  renderSlotTabs();
  renderProgressUI(slot);
  appendLog(`[${getTimeString()}] 🚀 Initiating generation for ${slot.name}...`, 'system');

  // 2. Dispatch to GPU with real-time upload progress tracking
  await dispatchSlotToGPU(slot);
}

function dataURItoBlob(dataURI) {
  if (!dataURI) return null;
  try {
    const parts = dataURI.split(',');
    const byteString = atob(parts[1]);
    const mimeString = parts[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
  } catch (e) {
    console.error('dataURItoBlob error:', e);
    return null;
  }
}

async function getBlobFromDataUrlOrPath(dataUrl) {
  if (!dataUrl) return null;
  try {
    const res = await fetch(dataUrl);
    if (res.ok) return await res.blob();
  } catch (e) {
    console.warn("Could not fetch blob from url/path:", e);
  }
  return dataURItoBlob(dataUrl);
}

async function dispatchSlotToGPU(slot) {
  try {
    let imageBlob = slot.imageFile;
    if (!imageBlob && slot.imageDataUrl) {
      imageBlob = await getBlobFromDataUrlOrPath(slot.imageDataUrl);
    } else if (!imageBlob && slot.imageUrl) {
      imageBlob = await getBlobFromDataUrlOrPath(slot.imageUrl);
    }

    let audioBlob = slot.audioFile;
    if (!audioBlob && slot.audioDataUrl) {
      audioBlob = await getBlobFromDataUrlOrPath(slot.audioDataUrl);
    } else if (!audioBlob && slot.audioUrl) {
      audioBlob = await getBlobFromDataUrlOrPath(slot.audioUrl);
    }

    if (!slot.imageAssetId && (!imageBlob || imageBlob.size < 100)) {
      slot.status = 'error';
      slot.stage = 'Missing or invalid face portrait image';
      alert('❌ Portrait photo is missing or corrupted. Please upload a photo.');
      updateButtonStates(slot);
      renderSlotTabs();
      renderProgressUI(slot);
      return;
    }

    const hasValidAudio = Boolean(slot.audioLibraryFilename || slot.audioAssetId || (audioBlob && audioBlob.size >= 100));
    if (!hasValidAudio) {
      slot.status = 'error';
      slot.stage = 'Missing or invalid voiceover audio';
      alert('❌ Speech audio voiceover is missing or corrupted. Please upload or select an audio file.');
      updateButtonStates(slot);
      renderSlotTabs();
      renderProgressUI(slot);
      return;
    }

    // If background pre-upload is currently running, wait briefly (up to 2.5s) to take advantage of zero-upload
    if (slot.imageUploading && slot.imageUploadPromise) {
      await Promise.race([slot.imageUploadPromise, new Promise(r => setTimeout(r, 2500))]);
    }
    if (slot.audioUploading && slot.audioUploadPromise) {
      await Promise.race([slot.audioUploadPromise, new Promise(r => setTimeout(r, 2500))]);
    }

    slot.status = 'submitting';
    slot.stage = 'Connecting & uploading assets to server...';
    slot.progress = 0;
    slot.uploadProgress = 0;
    slot.uploadProgressText = 'Starting upload...';
    slot.logs = [];
    slot.taskData = null;
    slot.taskId = null;
    slot.outputVideoUrl = null;
    slot.outputFilename = null;
    slot.fileSizeMb = null;
    slot.outputVideoUrl720p = null;
    slot.outputFilename720p = null;
    slot.fileSize720pMb = null;
    slot.durationFormatted = null;
    slot.generationTimeFormatted = null;
    updateButtonStates(slot);
    renderSlotTabs();
    renderProgressUI(slot);

    const formData = new FormData();
    if (slot.imageAssetId) {
      formData.append('image_asset_id', slot.imageAssetId);
    } else {
      formData.append('image_file', imageBlob, slot.imageName || 'portrait.jpg');
    }

    if (slot.audioLibraryFilename) {
      formData.append('audio_library_filename', slot.audioLibraryFilename);
      if (slot.audioAssetId) formData.append('audio_asset_id', slot.audioAssetId);
    } else if (slot.audioAssetId) {
      formData.append('audio_asset_id', slot.audioAssetId);
    } else {
      formData.append('audio_file', audioBlob, slot.audioName || 'speech.wav');
    }

    const effectiveRatio = (slot.selectedRatio === 'auto') ? (slot.detectedRatio || '9:16') : (slot.selectedRatio || '9:16');
    const checkedNeural = document.querySelector('input[name="neuralDiffusion"]:checked');
    const effectiveResolution = (checkedNeural && checkedNeural.value) ? checkedNeural.value : (slot.selectedResolution || '500p');
    slot.selectedResolution = effectiveResolution;
    slot.generationMode = 'anchor_seamless';

    formData.append('slot_name', slot.name || 'Video 1');
    formData.append('video_title', slot.title || '');
    formData.append('prompt', slot.prompt);
    formData.append('negative_prompt', slot.negativePrompt || '');
    formData.append('aspect_ratio', effectiveRatio);
    formData.append('resolution', effectiveResolution);
    formData.append('preset', slot.selectedPreset || 'distill_bf16');
    formData.append('gender', slot.gender || 'male');
    formData.append('num_inference_steps', slot.selectedSteps || 3);
    formData.append('num_frames', slot.numFrames || 205);
    formData.append('generation_mode', 'anchor_seamless');
    formData.append('transition_overlap_frames', 4);
    formData.append('hand_control', slot.handControl || 'natural');
    formData.append('length_mode', slot.lengthMode || 'auto');
    formData.append('seed', slot.seed || '10');

    // Reset previous completed output if user is re-generating
    slot.outputVideoUrl = null;
    slot.outputFilename = null;
    slot.fileSizeMb = null;
    slot.outputVideoUrl720p = null;
    slot.outputFilename720p = null;
    slot.fileSize720pMb = null;

    // Send with live upload progress callback!
    const data = await uploadAndGenerateSlot(formData, (pct, loadedMB, totalMB, speedStr, etaStr) => {
      slot.uploadProgress = pct;
      slot.uploadLoadedMB = loadedMB;
      slot.uploadTotalMB = totalMB;
      slot.uploadSpeedStr = speedStr;
      slot.uploadEtaStr = etaStr;
      const extraInfo = [speedStr, etaStr].filter(Boolean).join(' • ');
      slot.uploadProgressText = `Uploading: ${loadedMB}MB / ${totalMB}MB (${pct}%)${extraInfo ? ' • ' + extraInfo : ''}`;
      slot.stage = `Uploading Voiceover: ${loadedMB}MB / ${totalMB}MB (${pct}%)${extraInfo ? ' • ' + extraInfo : ''}`;
      updateButtonStates(slot);
      renderSlotTabs();
      renderProgressUI(slot);
    });

    slot.taskId = data.task_id;
    slot.status = (data.status === 'queued') ? 'queued' : 'running';
    slot.stage = (data.status === 'queued') ? 'Queued in background (Waiting for GPU turn)' : 'Initializing PyTorch on GPU...';
    slot.progress = (data.status === 'queued') ? 0.0 : 5.0;

    if (data.status === 'queued') {
      appendLog(`[${getTimeString()}] 🟡 ${slot.name} enqueued into server queue! Task ID: ${data.task_id} (Will render automatically)`, 'info');
    } else {
      appendLog(`[${getTimeString()}] 🟢 ${slot.name} started on GPU! Task ID: ${data.task_id} (${data.num_segments || 1} segments)`, 'success');
    }

    startSlotMonitor(slot);
    saveStudioState();
    fetchQueueStatus();
    updateButtonStates(slot);
    renderSlotTabs();
    renderProgressUI(slot);

  } catch (err) {
    slot.status = 'error';
    slot.stage = `Failed: ${err.message}`;
    appendLog(`[${getTimeString()}] [ERROR] Task submission failed for ${slot.name}: ${err.message}`, 'error');
    updateButtonStates(slot);
    renderSlotTabs();
    renderProgressUI(slot);
  }
}

function startSlotMonitor(slot) {
  if (!slot) return;
  if (slot.status === 'completed' || slot.status === 'cancelled' || slot.status === 'idle' || slot.outputVideoUrl) {
    if (slot.pollInterval) clearInterval(slot.pollInterval);
    if (slot.elapsedInterval) clearInterval(slot.elapsedInterval);
    slot.pollInterval = null;
    slot.elapsedInterval = null;
    return;
  }

  // Prevent duplicate concurrent polling intervals for the same slot
  if (slot.pollInterval) {
    return;
  }

  if (slot.elapsedInterval) {
    clearInterval(slot.elapsedInterval);
    slot.elapsedInterval = null;
  }

  if (!slot.generationStartTime) {
    const initElapsed = (slot.taskData && slot.taskData.elapsed_gpu_sec) ? slot.taskData.elapsed_gpu_sec : 0;
    slot.generationStartTime = Date.now() - (initElapsed * 1000);
  }

  slot.elapsedInterval = setInterval(() => {
    if (slot.generationStartTime) {
      slot.elapsed_gpu_sec = Math.floor((Date.now() - slot.generationStartTime) / 1000);
    }
    const active = getActiveSlot();
    if (active && active.id === slot.id) {
      renderProgressUI(active);
    }
  }, 1000);

  const pollFn = async () => {
    if (!slot.taskId || slot.status === 'idle' || slot.status === 'cancelled') {
      if (slot.pollInterval) clearInterval(slot.pollInterval);
      if (slot.elapsedInterval) clearInterval(slot.elapsedInterval);
      slot.pollInterval = null;
      slot.elapsedInterval = null;
      return;
    }

    try {
      const res = await fetch(`/api/task/${slot.taskId}`);
      if (!res.ok) return;

      const task = await res.json();
      slot.taskData = task;
      slot.progress = task.progress || 0.0;
      slot.stage = task.stage || 'Processing';
      slot.logs = task.logs || [];
      if (task.elapsed_gpu_sec) {
        slot.elapsed_gpu_sec = task.elapsed_gpu_sec;
        slot.generationStartTime = Date.now() - (task.elapsed_gpu_sec * 1000);
      }

      if (task.status === 'processing') {
        slot.status = 'running';
      } else if (task.status === 'queued') {
        slot.status = 'queued';
      } else if (task.status === 'completed') {
        slot.status = 'completed';
        slot.outputVideoUrl = task.output_video_url;
        slot.outputFilename = task.output_filename;
        slot.fileSizeMb = task.file_size_mb;
        slot.outputVideoUrl720p = task.output_video_url_720p;
        slot.outputFilename720p = task.output_filename_720p;
        slot.fileSize720pMb = task.file_size_720p_mb;
        slot.durationFormatted = task.audio_duration_formatted;
        slot.generationTimeFormatted = task.generation_time_formatted;

        if (slot.pollInterval) clearInterval(slot.pollInterval);
        if (slot.elapsedInterval) clearInterval(slot.elapsedInterval);
        slot.pollInterval = null;
        slot.elapsedInterval = null;

        lastRenderedGalleryKey = '';
        if (slot.id === studioState.activeSlotId && !slot.hasHandledCompletion) {
          slot.hasHandledCompletion = true;
          loadRenderedVideo(
            slot.outputVideoUrl,
            slot.outputFilename,
            slot.fileSizeMb,
            false,
            slot.name,
            slot.durationFormatted,
            slot.generationTimeFormatted,
            slot.outputVideoUrl720p,
            slot.outputFilename720p,
            slot.fileSize720pMb
          );
          const playerCard = $('renderedVideoCard');
          if (playerCard && !slot.hasScrolledToOutput) {
            slot.hasScrolledToOutput = true;
            playerCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        }

        appendLog(`[${getTimeString()}] 🎉 ${slot.name} Finished! Output: ${task.output_filename}`, 'success', slot);
        await fetchGallery();
        await fetchQueueStatus();

      } else if (task.status === 'cancelled') {
        slot.status = 'idle';
        if (slot.pollInterval) clearInterval(slot.pollInterval);
        if (slot.elapsedInterval) clearInterval(slot.elapsedInterval);
        slot.pollInterval = null;
        slot.elapsedInterval = null;
        slot.taskId = null;
        slot.progress = 0.0;
        slot.stage = task.stage || 'Cancelled by user';
        appendLog(`[${getTimeString()}] 🛑 ${slot.name} stopped: ${task.stage}`, 'info', slot);
        if (task.output_video_url) {
          slot.outputVideoUrl = task.output_video_url;
          slot.outputFilename = task.output_filename;
          slot.fileSizeMb = task.file_size_mb;
        }
        await fetchGallery();
        await fetchQueueStatus();

      } else if (task.status === 'error') {
        slot.status = 'error';
        if (slot.pollInterval) clearInterval(slot.pollInterval);
        if (slot.elapsedInterval) clearInterval(slot.elapsedInterval);
        slot.pollInterval = null;
        slot.elapsedInterval = null;
        appendLog(`[${getTimeString()}] 🛑 ${slot.name} stopped: ${task.stage}`, 'error', slot);
        fetchQueueStatus();
      }

      renderSlotTabs();
      const currentActive = getActiveSlot();
      if (currentActive) {
        renderProgressUI(currentActive);
        renderTerminalLogs(currentActive.logs || []);
        updateButtonStates(currentActive);
      }

      saveStudioState();

    } catch (e) {
      console.warn(`Polling error for ${slot.name}:`, e);
    }
  };

  pollFn();
  slot.pollInterval = setInterval(pollFn, 1500);
}

async function stopSlotGeneration(slot = getActiveSlot()) {
  if (!slot) return;

  const targetTaskId = slot.taskId || 'current';

  // INSTANT 0ms UI RESET:
  if (slot.pollInterval) clearInterval(slot.pollInterval);
  if (slot.elapsedInterval) clearInterval(slot.elapsedInterval);
  slot.pollInterval = null;
  slot.elapsedInterval = null;

  slot.status = 'idle';
  slot.taskId = null;
  slot.progress = 0.0;
  slot.stage = 'Cancelled by user · Ready';
  slot.hasHandledCompletion = false;
  slot.hasScrolledToOutput = false;

  renderSlotTabs();
  renderProgressUI(slot);
  updateButtonStates(slot);

  appendLog(`[${getTimeString()}] 🛑 ${slot.name} cancelled. Stopping GPU process...`, 'info');
  saveStudioState();

  // Asynchronously request backend to cancel
  try {
    await fetch('/api/task/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: targetTaskId, slot_name: slot.name })
    });
    await fetchQueueStatus();
    await fetchGallery();
  } catch (e) {
    console.error("Cancel task error:", e);
  }
}

window.cancelSpecificTask = async function(taskId) {
  if (!taskId) return;
  try {
    const res = await fetch('/api/task/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId })
    });
    const data = await res.json();
    appendLog(`[${getTimeString()}] 🛑 Task ${taskId} cancelled: ${data.message || 'Success'}`, 'info');
    
    // Update local matching slots
    studioState.slots.forEach(s => {
      if (s.taskId === taskId) {
        if (s.pollInterval) clearInterval(s.pollInterval);
        if (s.elapsedInterval) clearInterval(s.elapsedInterval);
        s.pollInterval = null;
        s.elapsedInterval = null;
        s.status = 'idle';
        s.taskId = null;
        s.progress = 0;
        s.stage = 'Cancelled by user';
        s.hasHandledCompletion = false;
        s.hasScrolledToOutput = false;
      }
    });
    renderSlotTabs();
    const active = getActiveSlot();
    if (active) {
      renderProgressUI(active);
      updateButtonStates(active);
    }
    saveStudioState();
    fetchQueueStatus();
  } catch (err) {
    console.error("Error cancelling task:", err);
  }
};

function updateButtonStates(slot = getActiveSlot()) {
  const btnGenerate = $('btnGenerateAvatar');
  const btnStop = $('btnStopGeneration');
  const btnFloatGen = $('floatingBtnGenerate');
  const floatBtnText = $('floatingBtnText');
  const floatBtnProgress = $('floatingBtnProgress');
  const btnFloatStop = $('floatingBtnStop');
  const dockSlotText = $('dockSlotText');

  const isSlotBusy = slot && (slot.status === 'running' || slot.status === 'queued' || slot.status === 'submitting');
  const isAnyBusy = isSlotBusy || studioState.hasActiveBackendTask || studioState.slots.some(s => s.status === 'running' || s.status === 'queued' || s.status === 'submitting');

  if (dockSlotText && slot) {
    dockSlotText.textContent = slot.name || 'Video 1';
  }

  if (btnGenerate) {
    btnGenerate.disabled = isSlotBusy;
    if (slot && slot.status === 'submitting') {
      btnGenerate.innerHTML = `<span class="badge-icon-spin">📤</span> <span class="btn-text">${slot.uploadProgressText || 'Uploading Audio...'}</span>`;
    } else if (isSlotBusy) {
      btnGenerate.innerHTML = `<span class="badge-icon-spin">⏳</span> <span class="btn-text">${slot.status === 'queued' ? 'In Queue...' : 'Generating Avatar...'}</span>`;
    } else if (slot && (slot.status === 'completed' || slot.outputVideoUrl)) {
      btnGenerate.innerHTML = `<span class="btn-icon">🔄</span> <span class="btn-text">Re-Generate Video</span>`;
    } else {
      btnGenerate.innerHTML = `<span class="btn-icon">⚡</span> <span class="btn-text">Generate Video</span>`;
    }
  }

  if (btnFloatGen) {
    btnFloatGen.disabled = isSlotBusy;
    if (slot && slot.status === 'running') {
      if (floatBtnText) floatBtnText.textContent = 'Generating';
      if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    } else if (slot && slot.status === 'queued') {
      if (floatBtnText) floatBtnText.textContent = 'In Queue...';
      if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    } else if (slot && (slot.status === 'completed' || slot.outputVideoUrl)) {
      if (floatBtnText) floatBtnText.textContent = 'Re-Generate';
      if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    } else {
      if (floatBtnText) floatBtnText.textContent = 'Generate Video';
      if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    }
  }

  if (btnStop) {
    btnStop.disabled = !isAnyBusy;
    if (isAnyBusy) {
      btnStop.style.opacity = '1';
      btnStop.style.cursor = 'pointer';
      btnStop.style.backgroundColor = '#ef4444';
      btnStop.style.color = '#ffffff';
      btnStop.style.borderColor = '#dc2626';
      btnStop.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg><span>Cancel / Stop Job</span>`;
    } else {
      btnStop.style.opacity = '0.5';
      btnStop.style.cursor = 'not-allowed';
      btnStop.style.backgroundColor = '';
      btnStop.style.color = '';
      btnStop.style.borderColor = '';
      btnStop.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg><span>Stop</span>`;
    }
  }

  if (btnFloatStop) {
    btnFloatStop.disabled = !isAnyBusy;
    btnFloatStop.style.display = isAnyBusy ? 'inline-flex' : 'none';
  }

  keepFloatingDockInBounds();
}

function keepFloatingDockInBounds() {
  const dock = $('floatingActionDock');
  if (!dock) return;
  requestAnimationFrame(() => {
    const pad = 14;
    const rect = dock.getBoundingClientRect();
    if (rect.right > window.innerWidth - pad) {
      const overflow = rect.right - (window.innerWidth - pad);
      let newLeft = rect.left - overflow;
      if (newLeft < pad) newLeft = pad;
      dock.style.left = `${newLeft}px`;
      dock.style.right = 'auto';
    }
  });
}

function initFloatingDockDragAndActions() {
  const dock = $('floatingActionDock');
  const btnFloatGen = $('floatingBtnGenerate');
  const btnFloatStop = $('floatingBtnStop');

  if (!dock) return;

  window.addEventListener('resize', keepFloatingDockInBounds);

  // Restore saved dock position if available
  const savedPos = localStorage.getItem('longcat_dock_position');
  if (savedPos) {
    try {
      const { x, y } = JSON.parse(savedPos);
      const maxX = Math.max(10, window.innerWidth - 240);
      const maxY = Math.max(10, window.innerHeight - 60);
      const clampX = Math.max(10, Math.min(x, maxX));
      const clampY = Math.max(10, Math.min(y, maxY));
      dock.style.left = `${clampX}px`;
      dock.style.top = `${clampY}px`;
      dock.style.right = 'auto';
      dock.style.bottom = 'auto';
    } catch (e) {}
  }

  // Floating button clicks
  if (btnFloatGen) {
    btnFloatGen.addEventListener('click', (e) => {
      e.stopPropagation();
      startActiveSlotGeneration();
    });
  }

  if (btnFloatStop) {
    btnFloatStop.addEventListener('click', (e) => {
      e.stopPropagation();
      const slot = getActiveSlot();
      if (confirm(`Are you sure you want to stop generation for ${slot.name}?`)) {
        stopSlotGeneration(slot);
      }
    });
  }

  // Robust Native Pointer Drag & Drop (Mouse Hold & Drag, Instant Release on MouseUp)
  let isDragging = false;
  let startX = 0;
  let startY = 0;
  let initialLeft = 0;
  let initialTop = 0;
  let hasMoved = false;

  dock.addEventListener('pointerdown', (e) => {
    // Only drag with primary mouse button (left click) or single touch
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    // Don't drag if clicking directly on buttons
    if (e.target.closest('button') || e.target.closest('a')) return;

    isDragging = true;
    hasMoved = false;
    startX = e.clientX;
    startY = e.clientY;

    const rect = dock.getBoundingClientRect();
    initialLeft = rect.left;
    initialTop = rect.top;

    try {
      dock.setPointerCapture(e.pointerId);
    } catch (err) {}
    dock.classList.add('is-dragging');
  });

  dock.addEventListener('pointermove', (e) => {
    if (!isDragging) return;
    // Safety check: If mouse button is no longer pressed, terminate drag immediately
    if (e.pointerType === 'mouse' && (e.buttons & 1) === 0) {
      endDrag(e);
      return;
    }

    const deltaX = e.clientX - startX;
    const deltaY = e.clientY - startY;

    if (Math.abs(deltaX) > 2 || Math.abs(deltaY) > 2) {
      hasMoved = true;
    }

    let newLeft = initialLeft + deltaX;
    let newTop = initialTop + deltaY;

    const pad = 10;
    const maxLeft = Math.max(pad, window.innerWidth - dock.offsetWidth - pad);
    const maxTop = Math.max(pad, window.innerHeight - dock.offsetHeight - pad);

    newLeft = Math.max(pad, Math.min(newLeft, maxLeft));
    newTop = Math.max(pad, Math.min(newTop, maxTop));

    dock.style.left = `${newLeft}px`;
    dock.style.top = `${newTop}px`;
    dock.style.right = 'auto';
    dock.style.bottom = 'auto';
  });

  function endDrag(e) {
    if (!isDragging) return;
    isDragging = false;
    dock.classList.remove('is-dragging');

    if (e && e.pointerId !== undefined) {
      try {
        dock.releasePointerCapture(e.pointerId);
      } catch (err) {}
    }

    if (hasMoved) {
      const rect = dock.getBoundingClientRect();
      localStorage.setItem('longcat_dock_position', JSON.stringify({
        x: Math.round(rect.left),
        y: Math.round(rect.top)
      }));
    }
  }

  dock.addEventListener('pointerup', endDrag);
  dock.addEventListener('pointercancel', endDrag);
  window.addEventListener('blur', () => endDrag());
}

function formatHumanDuration(seconds) {
  if (isNaN(seconds) || seconds <= 0) return '0s';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}h ${mins}m ${secs}s`;
  }
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

function parseTqdmTimeString(str) {
  if (!str) return 0;
  const parts = str.split(':').map(Number);
  if (parts.length === 2) {
    return (parts[0] * 60) + parts[1];
  } else if (parts.length === 3) {
    return (parts[0] * 3600) + (parts[1] * 60) + parts[2];
  }
  return 0;
}

function parseLogsAndCalculateTelemetry(slot, logs = [], task = {}) {
  const stepsPerSegment = parseInt(task.steps_per_segment || (slot.taskData && slot.taskData.steps_per_segment) || slot.selectedSteps || 3, 10);
  let totalSegments = parseInt(task.total_segments || task.num_segments || task.segments || (slot.taskData && (slot.taskData.total_segments || slot.taskData.num_segments || slot.taskData.segments)) || slot.num_segments || slot.total_segments || slot.selectedSegments || 1, 10);
  
  if (totalSegments <= 1 && slot.audioDuration && slot.audioDuration > 10) {
    totalSegments = Math.ceil(slot.audioDuration / 8);
  }
  
  let currentSegment = parseInt(task.current_segment || (slot.taskData && slot.taskData.current_segment) || slot.currentSegment || 1, 10);
  let currentStep = parseInt(task.current_step || (slot.taskData && slot.taskData.current_step) || slot.currentStep || 1, 10);

  const totalPipelineSteps = (task.total_pipeline_steps && task.total_pipeline_steps > 0) ? task.total_pipeline_steps : Math.max(1, totalSegments * stepsPerSegment);
  const completedSteps = (task.completed_steps !== undefined && task.completed_steps !== null)
    ? task.completed_steps 
    : Math.min(totalPipelineSteps, Math.max(0, ((currentSegment - 1) * stepsPerSegment) + currentStep));
  const remainingSteps = (task.remaining_steps !== undefined && task.remaining_steps !== null)
    ? task.remaining_steps 
    : Math.max(0, totalPipelineSteps - completedSteps);

  let stepLatency = task.step_latency || (slot.taskData && slot.taskData.step_latency) || slot.lastMeasuredStepLatency || 34.0;
  if (stepLatency && stepLatency > 0) slot.lastMeasuredStepLatency = stepLatency;

  // Determine if diffusion or postprocessing has already begun or finished
  const hasStartedDiffusion = completedSteps > 0 || currentSegment > 1 || (task.progress && task.progress > 8.0);
  const isPostProcessing = (task.stage && (task.stage.includes('Packaging') || task.stage.includes('Master') || task.stage.includes('Saving') || task.stage.includes('Finalizing'))) || task.status === 'completed';

  // Scan live logs for audio preprocessing vs diffusion
  const logLen = logs.length;
  let isAudioPreproc = false;
  let audioPreprocProgress = 0;
  let audioElapsedSec = 0;
  let audioRemainingSec = 0;
  let audioSpeedStr = '';

  // Audio preprocessing ONLY occurs at the very start before diffusion has started!
  if (!hasStartedDiffusion && !isPostProcessing) {
    for (let i = logLen - 1; i >= Math.max(0, logLen - 40); i--) {
      const line = logs[i] || '';
      if (line.includes('Denoising:') || line.includes('Generating segment') || line.includes('Saving video')) {
        isAudioPreproc = false;
        break;
      }
      // Strictly ensure this is vocal separation, NOT PyTorch weights loading or checkpointing!
      if (line.includes('Loading weights') || line.includes('checkpoint') || line.includes('Saving video') || line.includes('video:')) {
        continue;
      }
      const audioMatch = line.match(/(\d+)%\|.*?\|\s*(\d+)\/(\d+)\s*\[([\d:]+)<([\d:]+)(?:,\s*([\d\.]+)\s*(s\/it|it\/s))?/);
      if (audioMatch && (line.includes('MDX') || line.includes('Kim_Vocal') || line.includes('Vocal') || line.includes('audio') || line.includes('Separation'))) {
        isAudioPreproc = true;
        audioPreprocProgress = parseFloat(audioMatch[1]);
        audioElapsedSec = parseTqdmTimeString(audioMatch[4]);
        audioRemainingSec = parseTqdmTimeString(audioMatch[5]);
        if (audioMatch[6]) {
          const rawSpd = parseFloat(audioMatch[6]);
          const unit = (audioMatch[7] || 's/it').toLowerCase();
          const lat = unit.includes('it/s') ? (1.0 / rawSpd) : rawSpd;
          audioSpeedStr = `${lat.toFixed(1)}s / chunk`;
        }
        break;
      }
    }
  }

  let elapsedSec = 0;
  let estRemainingSec = 0;
  let totalEstSec = 0;
  let calculatedProgress = 0;

  if (task.status === 'completed') {
    calculatedProgress = 100.0;
    elapsedSec = task.generation_time_sec || slot.elapsed_gpu_sec || 0;
    estRemainingSec = 0;
    totalEstSec = elapsedSec;
  } else if (isPostProcessing) {
    calculatedProgress = 99.5;
    elapsedSec = (task.elapsed_gpu_sec && task.elapsed_gpu_sec > 0) ? task.elapsed_gpu_sec : ((slot.taskData && slot.taskData.elapsed_gpu_sec) || slot.elapsed_gpu_sec || task.generation_time_sec || Math.round(completedSteps * stepLatency));
    estRemainingSec = 5;
    totalEstSec = elapsedSec + estRemainingSec;
  } else if (isAudioPreproc) {
    elapsedSec = audioElapsedSec || task.elapsed_gpu_sec || slot.elapsed_gpu_sec || 60;
    const diffusionEstSec = Math.round(totalPipelineSteps * (stepLatency || 34.0));
    estRemainingSec = audioRemainingSec + diffusionEstSec;
    totalEstSec = elapsedSec + estRemainingSec;
    calculatedProgress = Math.min(7.0, Math.max(1.0, (audioPreprocProgress / 100) * 7.0));
  } else {
    elapsedSec = (task.elapsed_gpu_sec && task.elapsed_gpu_sec > 0) ? task.elapsed_gpu_sec : ((slot.taskData && slot.taskData.elapsed_gpu_sec) || slot.elapsed_gpu_sec || task.generation_time_sec || Math.round(completedSteps * stepLatency));
    estRemainingSec = (task.remaining_sec !== undefined && task.remaining_sec !== null) ? task.remaining_sec : Math.max(0, Math.round(remainingSteps * stepLatency));
    totalEstSec = (task.total_est_sec !== undefined && task.total_est_sec !== null && task.total_est_sec > 0) ? task.total_est_sec : (elapsedSec + estRemainingSec);
    calculatedProgress = Math.min(99.0, Math.max(8.0, 8.0 + ((completedSteps / totalPipelineSteps) * 91.0)));
  }

  const isRecovering = !!(task.is_recovering || (task.stage && (task.stage.includes('Auto-Recovery') || task.stage.includes('COLLAPSE') || task.stage.includes('Re-anchoring'))));

  // MONOTONIC SAFEGUARD: Progress should never regress backward unless auto-recovering!
  if (!isRecovering && slot.progress && slot.progress > calculatedProgress && slot.taskId && slot.taskId === (task.task_id || task.id)) {
    calculatedProgress = slot.progress;
  }

  return {
    isAudioPreproc,
    audioPreprocProgress,
    audioSpeedStr,
    isRecovering,
    currentSegment,
    totalSegments,
    currentStep,
    stepsPerSegment,
    completedSteps,
    totalPipelineSteps,
    remainingSteps,
    stepLatency,
    elapsedSec,
    estRemainingSec,
    totalEstSec,
    calculatedProgress
  };
}

function renderProgressUI(slot = getActiveSlot()) {
  const activeSlot = getActiveSlot();
  if (!activeSlot) return;

  // STRICT TAB ISOLATION: If a specific slot is passed (e.g. background upload or background monitor poll),
  // NEVER touch the monitor DOM unless that slot is the currently active tab!
  if (slot && slot.id !== activeSlot.id) {
    return;
  }
  const currentSlot = slot || activeSlot;

  const fill = $('progressBarFill');
  const percentEl = $('progressPercentDisplay');
  const badge = $('progressStatusBadge');
  const badgeText = $('progressStatusText');
  const spinIcon = $('progressSpinIcon');

  const elapsedEl = $('metricElapsed');
  const etaEl = $('metricEta');
  const totalEl = $('metricTotal');
  const segmentEl = $('metricSegment');
  const stepsEl = $('metricSteps');
  const stageEl = $('metricStage');

  const floatBtnText = $('floatingBtnText');
  const floatBtnProgress = $('floatingBtnProgress');
  const dockSlotText = $('dockSlotText');

  if (dockSlotText) {
    dockSlotText.textContent = currentSlot.name || 'Video 1';
  }

  if (currentSlot.status === 'running') {
    const telemetry = parseLogsAndCalculateTelemetry(currentSlot, currentSlot.logs || [], currentSlot.taskData || {});
    currentSlot.progress = telemetry.calculatedProgress;

    if (fill) fill.style.width = `${currentSlot.progress.toFixed(1)}%`;
    if (percentEl) {
      if (telemetry.isAudioPreproc) {
        percentEl.textContent = `${currentSlot.progress.toFixed(1)}% (Stage 1/3: Vocal Audio Cleaning · ${telemetry.audioPreprocProgress.toFixed(0)}%)`;
      } else if (telemetry.isRecovering) {
        const stepDisplay = telemetry.currentStep > 0 ? `Step ${telemetry.currentStep}/${telemetry.stepsPerSegment}` : `Step 1/${telemetry.stepsPerSegment}`;
        percentEl.textContent = `${currentSlot.progress.toFixed(1)}% (🛡️ Auto-Recovery Seg ${telemetry.currentSegment}/${telemetry.totalSegments} · ${stepDisplay})`;
      } else {
        const stepDisplay = telemetry.currentStep > 0 ? `Step ${telemetry.currentStep}/${telemetry.stepsPerSegment}` : `Preparing Step 1/${telemetry.stepsPerSegment}`;
        percentEl.textContent = `${currentSlot.progress.toFixed(1)}% (Segment ${telemetry.currentSegment}/${telemetry.totalSegments} · ${stepDisplay})`;
      }
    }

    if (floatBtnText) floatBtnText.textContent = telemetry.isAudioPreproc ? 'Audio Prep' : 'Generating';
    if (floatBtnProgress) {
      floatBtnProgress.classList.add('hidden');
    }

    // Ensure tab name label stays clean without duplicate percentage
    const tabNameEl = document.querySelector(`.video-tab-btn[data-slot-id="${currentSlot.id}"] .tab-name-label`);
    if (tabNameEl) {
      tabNameEl.textContent = `🎬 ${currentSlot.name}`;
    }

    // Update the single status badge pill with live percentage
    const tabBadgeEl = document.querySelector(`.video-tab-btn[data-slot-id="${currentSlot.id}"] .tab-badge-pill`);
    if (tabBadgeEl) {
      const pctVal = typeof currentSlot.progress === 'number' ? currentSlot.progress.toFixed(0) : parseFloat(currentSlot.progress || 0).toFixed(0);
      tabBadgeEl.className = 'tab-badge-pill badge-running';
      tabBadgeEl.innerHTML = `<span class="mini-pulse-dot"></span>${pctVal}%`;
    }

    if (elapsedEl) elapsedEl.textContent = formatHumanDuration(telemetry.elapsedSec);
    if (etaEl) etaEl.textContent = formatHumanDuration(telemetry.estRemainingSec);
    if (totalEl) totalEl.textContent = formatHumanDuration(telemetry.totalEstSec);
    
    if (segmentEl) {
      if (telemetry.isAudioPreproc) {
        segmentEl.textContent = `Vocal Prep (${telemetry.audioPreprocProgress.toFixed(0)}%) · 1 / ${telemetry.totalSegments}`;
      } else if (telemetry.isRecovering) {
        segmentEl.textContent = `🛡️ Auto-Recovery ${telemetry.currentSegment} / ${telemetry.totalSegments}`;
      } else {
        segmentEl.textContent = `${telemetry.currentSegment} / ${telemetry.totalSegments} (${telemetry.totalSegments - telemetry.currentSegment} Left)`;
      }
    }

    if (stepsEl) {
      if (telemetry.isAudioPreproc) {
        stepsEl.textContent = `Pre-processing Speech Audio`;
      } else {
        const stepDisplay = telemetry.currentStep > 0 ? `Step ${telemetry.currentStep} / ${telemetry.stepsPerSegment}` : `Step 0 / ${telemetry.stepsPerSegment} (Starting)`;
        stepsEl.textContent = `${stepDisplay} (Total: ${telemetry.completedSteps} / ${telemetry.totalPipelineSteps})`;
      }
    }

    if (stageEl) {
      if (telemetry.isAudioPreproc) {
        stageEl.textContent = telemetry.audioSpeedStr || '7.8s/chunk';
      } else {
        stageEl.textContent = `${telemetry.stepLatency.toFixed(1)}s/step`;
      }
    }

    if (badge) badge.className = 'progress-badge-status active';
    if (badgeText) {
      if (telemetry.isAudioPreproc) {
        badgeText.textContent = 'STAGE 1: AUDIO';
      } else if (telemetry.isRecovering) {
        badgeText.textContent = 'STAGE 2: RECOVERING';
      } else if (currentSlot.taskData && currentSlot.taskData.stage && currentSlot.taskData.stage.includes('Stage 3')) {
        badgeText.textContent = 'STAGE 3: MASTERING';
      } else {
        badgeText.textContent = 'STAGE 2: NEURAL DIT';
      }
    }
    if (spinIcon) spinIcon.classList.remove('hidden');

  } else if (currentSlot.status === 'submitting') {
    const pct = currentSlot.uploadProgress || 0;
    const loadedMB = currentSlot.uploadLoadedMB || '0.0';
    const totalMB = currentSlot.uploadTotalMB || currentSlot.audioSizeMb || '0.0';
    const speed = currentSlot.uploadSpeedStr || 'Uploading';
    const eta = currentSlot.uploadEtaStr || 'Calculating...';

    if (fill) fill.style.width = `${pct}%`;
    if (percentEl) percentEl.textContent = `${pct}% (📤 ${loadedMB}MB / ${totalMB}MB)`;
    if (floatBtnText) floatBtnText.textContent = `Uploading ${pct}%`;
    if (floatBtnProgress) {
      floatBtnProgress.classList.remove('hidden');
      floatBtnProgress.textContent = `${pct}%`;
    }
    if (elapsedEl) elapsedEl.textContent = 'Active';
    if (etaEl) etaEl.textContent = eta;
    if (totalEl) totalEl.textContent = speed;
    if (segmentEl) segmentEl.textContent = `${totalMB} MB`;
    if (stepsEl) stepsEl.textContent = 'Voiceover Upload';
    if (stageEl) stageEl.textContent = currentSlot.uploadProgressText || `Uploading Voiceover: ${loadedMB}MB / ${totalMB}MB (${pct}%)`;

    if (badge) badge.className = 'progress-badge-status active';
    if (badgeText) badgeText.textContent = `UPLOADING (${pct}%)`;
    if (spinIcon) spinIcon.classList.remove('hidden');

  } else if (currentSlot.status === 'queued') {
    if (fill) fill.style.width = '0%';
    if (percentEl) percentEl.textContent = '0.0% (⏳ Queued in Batch)';
    if (floatBtnText) floatBtnText.textContent = 'In Queue...';
    if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    if (elapsedEl) elapsedEl.textContent = '--:--';
    if (etaEl) etaEl.textContent = 'Waiting in queue...';
    if (totalEl) totalEl.textContent = '--:--';
    if (segmentEl) segmentEl.textContent = 'Queued';
    if (stepsEl) stepsEl.textContent = 'Queued';
    if (stageEl) stageEl.textContent = 'In Queue';

    if (badge) badge.className = 'progress-badge-status';
    if (badgeText) badgeText.textContent = 'QUEUED';
    if (spinIcon) spinIcon.classList.remove('hidden');

  } else if (currentSlot.status === 'completed') {
    if (fill) fill.style.width = '100%';
    if (percentEl) percentEl.textContent = '100% (Completed — Video Ready)';
    if (floatBtnText) floatBtnText.textContent = 'Re-Generate';
    if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    if (elapsedEl) elapsedEl.textContent = currentSlot.generationTimeFormatted || 'Done';
    if (etaEl) etaEl.textContent = '0s (Done)';
    if (totalEl) totalEl.textContent = currentSlot.generationTimeFormatted || 'Done';
    if (segmentEl) segmentEl.textContent = 'Complete';
    if (stepsEl) stepsEl.textContent = 'Complete';
    if (stageEl) stageEl.textContent = 'Completed';

    if (badge) badge.className = 'progress-badge-status active';
    if (badgeText) badgeText.textContent = 'COMPLETED';
    if (spinIcon) spinIcon.classList.add('hidden');

  } else if (currentSlot.status === 'error') {
    if (fill) fill.style.width = '0%';
    if (percentEl) percentEl.textContent = 'Error / Stopped';
    if (floatBtnText) floatBtnText.textContent = 'Generate Video';
    if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    if (elapsedEl) elapsedEl.textContent = '--:--';
    if (etaEl) etaEl.textContent = '--:--';
    if (totalEl) totalEl.textContent = '--:--';
    if (segmentEl) segmentEl.textContent = 'Error';
    if (stepsEl) stepsEl.textContent = 'Error';
    if (stageEl) stageEl.textContent = 'Error';

    if (badge) badge.className = 'progress-badge-status';
    if (badgeText) badgeText.textContent = 'ERROR';
    if (spinIcon) spinIcon.classList.add('hidden');

  } else {
    // idle
    if (fill) fill.style.width = '0%';
    if (percentEl) percentEl.textContent = '0.0% (Ready)';
    if (floatBtnText) floatBtnText.textContent = 'Generate Video';
    if (floatBtnProgress) floatBtnProgress.classList.add('hidden');
    if (elapsedEl) elapsedEl.textContent = '--:--';
    if (etaEl) etaEl.textContent = '--:--';
    if (totalEl) totalEl.textContent = '--:--';
    if (segmentEl) segmentEl.textContent = '0 / 0';
    if (stepsEl) stepsEl.textContent = '0 / 0';
    if (stageEl) stageEl.textContent = '--:--';

    if (badge) badge.className = 'progress-badge-status';
    if (badgeText) badgeText.textContent = 'IDLE';
    if (spinIcon) spinIcon.classList.add('hidden');
  }

  keepFloatingDockInBounds();
}

// ==========================================
// 7. Queue Monitor Dashboard Modal
// ==========================================
function openQueueMonitor() {
  const modal = $('queueMonitorModal');
  if (modal) {
    modal.classList.remove('hidden');
    fetchQueueStatus();
  }
}

function closeQueueMonitor(e) {
  if (e && e.target !== e.currentTarget && !e.target.classList.contains('modal-close-btn')) return;
  const modal = $('queueMonitorModal');
  if (modal) modal.classList.add('hidden');
}



async function fetchQueueStatus() {
  try {
    const [qRes, gRes] = await Promise.all([
      fetch('/api/queue'),
      fetch('/api/gallery')
    ]);
    const qData = qRes.ok ? await qRes.json() : {};
    const gData = gRes.ok ? await gRes.json() : { videos: [] };
    const videos = gData.videos || [];

    // Always update the Recent Videos gallery cards in real-time
    renderGalleryCards(videos);

    const activeList = qData.active_tasks || (qData.active_task ? [qData.active_task] : []);
    const queuedList = qData.queued_tasks || [];

    studioState.hasActiveBackendTask = (activeList.length > 0);

    // 1. Dynamic Video Matching for each slot from gallery (only for idle/completed slots, NEVER for busy slots)
    studioState.slots.forEach(slot => {
      // If this slot is actively running or queued on the server, NEVER overwrite from gallery!
      const isBusyOnServer = activeList.some(at => at.id === slot.taskId || at.slot_name === slot.name) ||
                             queuedList.some(qt => qt.id === slot.taskId || qt.slot_name === slot.name);

      if (isBusyOnServer || slot.status === 'running' || slot.status === 'queued' || slot.status === 'submitting') {
        return;
      }

      let matchedVideo = null;
      if (slot.outputFilename) {
        matchedVideo = videos.find(v => v.filename === slot.outputFilename || v.filename_1080p === slot.outputFilename);
      }
      if (!matchedVideo && slot.taskId) {
        matchedVideo = videos.find(v => (v.filename && v.filename.includes(slot.taskId)) || (v.id && v.id.includes(slot.taskId)));
      }
      if (!matchedVideo && slot.id === 1 && !slot.outputFilename && videos.length > 0) {
        matchedVideo = videos.find(v => v.filename && v.filename.startsWith('Video_1'));
      }

      if (matchedVideo) {
        slot.status = 'completed';
        slot.outputVideoUrl = matchedVideo.url_1080p || matchedVideo.url;
        slot.outputFilename = matchedVideo.filename_1080p || matchedVideo.filename;
        slot.fileSizeMb = matchedVideo.size_1080p_mb || matchedVideo.size_mb;
        slot.outputVideoUrl720p = matchedVideo.url_720p;
        slot.outputFilename720p = matchedVideo.filename_720p;
        slot.fileSize720pMb = matchedVideo.size_720p_mb;
        slot.durationFormatted = matchedVideo.duration_label;
        slot.generationTimeFormatted = matchedVideo.render_time_label;
      } else if (slot.outputFilename) {
        // File was deleted on server: cleanly clear slot output
        slot.status = 'idle';
        slot.outputVideoUrl = null;
        slot.outputFilename = null;
        slot.fileSizeMb = null;
        slot.outputVideoUrl720p = null;
        slot.outputFilename720p = null;
        if (slot.id === studioState.activeSlotId) {
          resetVideoPlayerUI(slot.name);
        }
      }
    });

    // 2. Sync active running tasks AND auto-attach to UI tabs (Studio tasks only)
    activeList.forEach(at => {
      let targetSlot = studioState.slots.find(s => s.taskId === at.id);
      if (!targetSlot && at.slot_name && at.slot_name !== 'Avatar Library') {
        targetSlot = studioState.slots.find(s => s.name === at.slot_name);
      }
      if (!targetSlot && at.slot_name && at.slot_name !== 'Avatar Library') {
        const slotNumMatch = at.slot_name.match(/\d+/);
        const num = slotNumMatch ? parseInt(slotNumMatch[0], 10) : (studioState.slots.length + 1);
        targetSlot = createSlot(num, at.slot_name);
        studioState.slots.push(targetSlot);
      }
      if (targetSlot) {
        targetSlot.taskId = at.id;
        targetSlot.taskData = at;
        targetSlot.status = 'running';
        targetSlot.progress = at.progress || targetSlot.progress || 0;
        targetSlot.stage = at.stage || 'Processing on GPU';
        if (at.logs && at.logs.length > 0) {
          targetSlot.logs = at.logs;
        }

        if (!targetSlot.pollInterval) {
          startSlotMonitor(targetSlot);
        }
        renderProgressUI(targetSlot);
        if (targetSlot.id === studioState.activeSlotId) {
          renderTerminalLogs(targetSlot.logs || []);
        }
      }
    });

    // Allow user to stay on inactive/idle slots (e.g. Video 2) to prepare tasks while Video 1 is running

    // Sync all queued tasks across all slots (Positions #1, #2, #3... up to #10) (Studio tasks only)
    queuedList.forEach((qt, idx) => {
      let targetSlot = studioState.slots.find(s => s.taskId === qt.id);
      if (!targetSlot && qt.slot_name && qt.slot_name !== 'Avatar Library') {
        targetSlot = studioState.slots.find(s => s.name === qt.slot_name);
      }
      if (!targetSlot && qt.slot_name && qt.slot_name !== 'Avatar Library') {
        const slotNumMatch = qt.slot_name.match(/\d+/);
        const num = slotNumMatch ? parseInt(slotNumMatch[0], 10) : (studioState.slots.length + 1);
        targetSlot = createSlot(num, qt.slot_name);
        studioState.slots.push(targetSlot);
      }
      if (targetSlot && targetSlot.status !== 'running' && targetSlot.status !== 'completed') {
        targetSlot.taskId = qt.id;
        targetSlot.taskData = qt;
        targetSlot.status = 'queued';
        targetSlot.progress = 0.0;
        targetSlot.stage = `In GPU Queue (Position #${idx + 1})`;
        if (!targetSlot.pollInterval) {
          startSlotMonitor(targetSlot);
        }
      }
    });

    const currentActiveSlot = getActiveSlot();
    if (currentActiveSlot) {
      if (currentActiveSlot.status === 'completed' && currentActiveSlot.outputVideoUrl) {
        const videoPlayer = $('mainVideoPlayer');
        const targetSrc = currentActiveSlot.outputVideoUrl720p || currentActiveSlot.outputVideoUrl;
        if (!videoPlayer || videoPlayer.dataset.loadedSrc !== targetSrc) {
          loadRenderedVideo(
            currentActiveSlot.outputVideoUrl,
            currentActiveSlot.outputFilename,
            currentActiveSlot.fileSizeMb,
            false,
            currentActiveSlot.name,
            currentActiveSlot.durationFormatted,
            currentActiveSlot.generationTimeFormatted,
            currentActiveSlot.outputVideoUrl720p,
            currentActiveSlot.outputFilename720p,
            currentActiveSlot.fileSize720pMb
          );
        }
      }
      renderProgressUI(currentActiveSlot);
      renderTerminalLogs(currentActiveSlot.logs || []);
    }

    // Periodically verify cross-device tab parity (e.g. laptop opened or closed a tab)
    if (!fetchQueueStatus._tick) fetchQueueStatus._tick = 0;
    fetchQueueStatus._tick++;
    if (fetchQueueStatus._tick % 2 === 0) {
      try {
        const ssRes = await fetch('/api/studio_state');
        if (ssRes.ok) {
          const serverState = await ssRes.json();
          if (serverState && Array.isArray(serverState.slots)) {
            const isUserTyping = document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA');
            if (!isUserTyping) {
              const serverIds = serverState.slots.map(s => s.id);
              const localIds = studioState.slots.map(s => s.id);
              const isDifferent = serverIds.length !== localIds.length || serverIds.some((id, i) => id !== localIds[i]);
              if (isDifferent) {
                const mergedSlots = serverState.slots.map(s => {
                  const existing = studioState.slots.find(loc => loc.id === s.id);
                  if (existing) {
                    return Object.assign(existing, s);
                  } else {
                    return Object.assign(createSlot(s.id, s.name), s);
                  }
                });
                studioState.slots = mergedSlots;
                if (!studioState.slots.some(s => s.id === studioState.activeSlotId)) {
                  studioState.activeSlotId = studioState.slots[0]?.id || 1;
                }
                renderSlotTabs();
                populateDOMFromActiveSlot();
              }
            }
          }
        }
      } catch (e) {}
    }

    renderQueueMonitorModal(qData, videos);
    updateQueueHeaderBadge(qData);
    renderSlotTabs();
    updateButtonStates();
  } catch (e) {
    console.warn('Queue fetch error:', e);
  }
}

function startQueueSync() {
  if (studioState.queuePollInterval) clearInterval(studioState.queuePollInterval);
  studioState.queuePollInterval = setInterval(fetchQueueStatus, 3000);
}

function updateQueueHeaderBadge(data) {
  const badge = $('queueHeaderBadge');
  if (!badge) return;

  const runningCount = studioState.slots.filter(s => s.status === 'running').length;
  const queuedCount = studioState.slots.filter(s => s.status === 'queued').length;

  if (runningCount > 0) {
    badge.textContent = `🟢 1/1 Running ${queuedCount > 0 ? `· 🟡 ${queuedCount} Queued` : ''}`;
    badge.style.background = 'rgba(16, 185, 129, 0.3)';
  } else if (queuedCount > 0) {
    badge.textContent = `🟡 ${queuedCount} Queued`;
    badge.style.background = 'rgba(245, 158, 11, 0.3)';
  } else {
    badge.textContent = `${studioState.slots.length} Tabs Ready`;
    badge.style.background = 'rgba(255, 255, 255, 0.2)';
  }
}

function getVideoCardInfo(v) {
  if (!v) return { slotLabel: 'Video', title: 'Video', fullDisplayTitle: 'Video' };

  const fn = v.filename_1080p || v.filename || '';
  let slotLabel = '';
  let cleanTitle = v.video_title || v.title || '';

  // 1. Check if filename starts with Video_1, Video_2, Video_3 etc.
  const slotMatch = fn.match(/^Video_(\d+)/i);
  let slotId = null;
  if (slotMatch) {
    slotId = parseInt(slotMatch[1]);
    slotLabel = `Video ${slotId}`;
  }

  // 2. Look up matched slot in studioState.slots
  let matchedSlot = null;
  if (slotId !== null) {
    matchedSlot = studioState.slots.find(s => s.id === slotId);
  }
  if (!matchedSlot) {
    matchedSlot = studioState.slots.find(s => 
      (s.outputFilename && (s.outputFilename === fn || s.outputFilename_720p === fn)) ||
      (s.taskId && (fn.includes(s.taskId) || (v.id && String(v.id).includes(s.taskId))))
    );
  }

  if (matchedSlot) {
    slotLabel = slotLabel || matchedSlot.name || `Video ${matchedSlot.id}`;
    if (!cleanTitle && matchedSlot.title) {
      cleanTitle = matchedSlot.title;
    }
  }

  // 3. If cleanTitle is still empty, parse cleanly from filename
  if (!cleanTitle) {
    let clean = fn.replace(/\.(mp4|mov|avi|webm)$/i, '');
    clean = clean.replace(/_720p$/i, '');
    clean = clean.replace(/^Video_\d+_/i, '');
    clean = clean.replace(/^Avatar_[a-f0-9]+/i, '').trim();
    clean = clean.replace(/_/g, ' ').replace(/-/g, ' ').trim();
    cleanTitle = clean || 'Rendered Video';
  }

  cleanTitle = cleanTitle.trim();
  // Strip duplicate "Video 1:" from cleanTitle if already prefixed
  if (slotLabel) {
    const pfxRegex = new RegExp(`^${slotLabel.replace(' ', '[_\\s]+')}\\s*[:-]?\\s*`, 'i');
    cleanTitle = cleanTitle.replace(pfxRegex, '').trim();
  }

  const fullDisplayTitle = slotLabel ? `${slotLabel}: ${cleanTitle}` : cleanTitle;

  return {
    slotLabel: slotLabel || 'Video',
    title: cleanTitle,
    fullDisplayTitle: fullDisplayTitle
  };
}

function formatShortVideoTitle(filename, maxWords = 25) {
  if (!filename) return 'Video';
  const info = getVideoCardInfo({ filename: filename });
  return info.fullDisplayTitle;
}

function getSlotLabelForTask(taskId, fallbackIdx = 1, taskData = null) {

  if (!taskId) return `Video ${fallbackIdx}`;
  const slot = studioState.slots.find(s => s.taskId === taskId);
  if (slot) {
    return `${slot.name}${slot.title ? ` (${slot.title})` : ''}`;
  }
  return `Video ${fallbackIdx}`;
}

function getSlotLabelForVideo(video, fallbackIdx = 1) {
  if (!video) return `Video ${fallbackIdx}`;
  const match = (video.filename || '').match(/^Video_(\d+)_/i);
  if (match) {
    return `Video ${match[1]}`;
  }
  return `Video ${fallbackIdx}`;
}

function renderQueueMonitorModal(data, completedVideos = []) {
  const body = $('queueModalBody');
  if (!body) return;

  const activeList = data.active_tasks || (data.active_task ? [data.active_task] : []);
  const queuedTasks = data.queued_tasks || [];
  const runningSlots = studioState.slots.filter(s => s.status === 'running');
  const queuedSlots = studioState.slots.filter(s => s.status === 'queued');

  body.innerHTML = `
    <!-- Stats Row -->
    <div class="queue-stats-row">
      <div class="queue-stat-card">
        <div class="queue-stat-num" style="color: var(--emerald-600);">${runningSlots.length || activeList.length}</div>
        <div class="queue-stat-label">Active Running</div>
      </div>
      <div class="queue-stat-card">
        <div class="queue-stat-num" style="color: #f59e0b;">${queuedTasks.length}</div>
        <div class="queue-stat-label">In Queue</div>
      </div>
      <div class="queue-stat-card">
        <div class="queue-stat-num" style="color: var(--primary-accent);">${completedVideos.length}</div>
        <div class="queue-stat-label">Rendered Videos</div>
      </div>
      <div class="queue-stat-card">
        <div class="queue-stat-num" style="color: var(--text-primary);">${studioState.slots.length}/5</div>
        <div class="queue-stat-label">Total Tabs</div>
      </div>
    </div>

    <!-- Active Task Section -->
    <div>
      <div class="queue-section-title">
        <span>🟢 Currently Rendering on NVIDIA RTX PRO 6000 (${activeList.length} Active Engine${activeList.length > 1 ? 's' : ''})</span>
      </div>
      ${activeList.length > 0 ? activeList.map((at, idx) => {
        const slotLabel = getSlotLabelForTask(at.id, idx + 1, at);
        return `
          <div class="queue-active-card" style="margin-bottom: 12px; background: #ffffff; border: 1px solid var(--border-strong); border-radius: var(--radius-lg); padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="gallery-meta-tag" style="background: var(--emerald-50); color: var(--emerald-700); font-weight: 700;">⚡ ${escapeHtml(slotLabel)}</span>
                <strong>Task ID: ${escapeHtml(at.id)}</strong>
              </div>
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-weight: 700; color: var(--emerald-600); font-size: 14px;">${at.progress ? at.progress.toFixed(1) : '0'}%</span>
                <button type="button" style="background: #ef4444; color: #ffffff; border: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;" onclick="event.stopPropagation(); if(confirm('Stop currently rendering task ${escapeHtml(at.id)}?')) cancelSpecificTask('${escapeHtml(at.id)}');">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg>
                  Stop Engine
                </button>
              </div>
            </div>
            <div style="font-size: 12px; color: var(--text-secondary); margin: 6px 0 3px 0;">
              ${escapeHtml(at.stage || 'Denoising on GPU...')}
            </div>
            <div class="progress-bar-track" style="margin: 6px 0; height: 6px;">
              <div class="progress-bar-fill" style="width: ${at.progress || 0}%;"></div>
            </div>
            <div style="display: flex; gap: 14px; font-size: 11px; color: var(--text-muted); margin-top: 4px;">
              <span>⏱️ Speed: ${at.step_speed_str || 'Calculating...'}</span>
              <span>⏳ Remaining: ${at.remaining_sec ? `${Math.round(at.remaining_sec)}s` : 'Estimating...'}</span>
              <span>🎬 Segments: ${at.segments}</span>
              <span>📐 Res: ${at.resolution}</span>
              <span>⚡ Steps: ${at.steps}</span>
            </div>
          </div>
        `;
      }).join('') : `
        <div style="padding: 16px; background: #f8fafc; border: 1px dashed var(--border-strong); border-radius: var(--radius-md); text-align: center; color: var(--text-muted); font-size: 13px;">
          GPU is currently idle and ready for incoming video jobs.
        </div>
      `}
    </div>

    <!-- Pending Queue Section -->
    <div>
      <div class="queue-section-title">
        <span>🟡 Sequential Queue (${queuedTasks.length} Pending)</span>
      </div>
      ${queuedTasks.length > 0 ? `
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${queuedTasks.map((t, idx) => {
            const slotLabel = getSlotLabelForTask(t.id, idx + 2, t);
            return `
              <div class="queue-item-row" style="display: flex; justify-content: space-between; align-items: center; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 10px 14px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span style="font-weight: 700; color: #f59e0b;">#${idx + 1}</span>
                  <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="gallery-meta-tag" style="background: #fef3c7; color: #92400e; font-weight: 700;">🟡 ${escapeHtml(slotLabel)}</span>
                      <strong>Task ID: ${escapeHtml(t.id)}</strong>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Queued at ${t.created_at || 'Queue'} · ${t.audio_duration} · ${t.resolution} · ${t.steps} steps</div>
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span class="gallery-meta-tag" style="background: #fef3c7; color: #92400e; font-weight: 700;">Waiting</span>
                  <button type="button" style="background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer;" onclick="event.stopPropagation(); if(confirm('Cancel task ${escapeHtml(t.id)} from queue?')) cancelSpecificTask('${escapeHtml(t.id)}');">
                    ✕ Cancel
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      ` : `
        <div style="padding: 14px; background: #f8fafc; border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); text-align: center; color: var(--text-muted); font-size: 12.5px;">
          No additional jobs waiting in queue.
        </div>
      `}
    </div>

    <!-- Completed & Rendered Videos with 2-Column Responsive Grid -->
    <div>
      <div class="queue-section-title" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span>🎬 Completed & Rendered Videos (${completedVideos.length})</span>
      </div>
      ${completedVideos.length > 0 ? `
        <div class="queue-completed-video-grid-2col">
          ${completedVideos.map((v, vIdx) => {
            const vSlotLabel = getSlotLabelForVideo(v, vIdx + 1);
            const safeUrl1080 = v.url_1080p || v.url || '';
            const safeUrl720 = v.url_720p || (safeUrl1080 ? safeUrl1080.replace('.mp4', '_720p.mp4') : '');
            const safeFn1080 = v.filename_1080p || v.filename || 'video.mp4';
            const safeFn720 = v.filename_720p || (safeFn1080 ? safeFn1080.replace('.mp4', '_720p.mp4') : 'video_720p.mp4');
            const s1080 = v.size_1080p_mb || v.size_mb || '0';
            const s720 = v.size_720p_mb || (Math.round((parseFloat(s1080) * 0.45) * 10) / 10) || '0';
            const shortTitle = formatShortVideoTitle(safeFn1080, 10);
            const dlUrl1080 = safeUrl1080 ? (safeUrl1080.includes('?') ? `${safeUrl1080}&download=1` : `${safeUrl1080}?download=1`) : '';
            const dlUrl720 = safeUrl720 ? (safeUrl720.includes('?') ? `${safeUrl720}&download=1` : `${safeUrl720}?download=1`) : '';

            return `
              <div class="queue-completed-video-card" style="background: #ffffff; border: 1px solid var(--border-strong); border-radius: var(--radius-lg); padding: 14px; box-shadow: 0 4px 14px rgba(0,0,0,0.06); display: flex; flex-direction: column; justify-content: space-between; position: relative;">
                
                <!-- Top Header: Title (6-7 words max), Slot Badge & Delete Button -->
                <div>
                  <div class="queue-card-header-top">
                    <div class="queue-card-title-box">
                      <span class="gallery-meta-tag" style="background: var(--emerald-50); color: var(--emerald-700); font-weight: 700; font-size: 11px; flex-shrink: 0;">✅ ${escapeHtml(vSlotLabel)}</span>
                      <strong class="queue-card-title" title="${escapeHtml(safeFn1080)}">${escapeHtml(shortTitle)}</strong>
                    </div>
                    
                    <!-- Quick Delete Button -->
                    <button type="button" class="btn-queue-action btn-action-delete" style="background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 12px; font-weight: bold; flex-shrink: 0;" title="Delete Video" onclick="event.stopPropagation(); if(confirm('Delete ${escapeHtml(safeFn1080)}?')) deleteSingleVideo('${escapeHtml(safeFn1080)}');">
                      ✕
                    </button>
                  </div>

                  <!-- Metadata Badges: Duration (Left), Resolution Engine (Center), Render Time (Right), Size -->
                  <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 10px;">
                    <span class="gallery-meta-tag gallery-duration-tag" style="font-size: 11px; padding: 2px 7px;" title="Exact Video Duration">⏱️ <strong>${v.duration_label || 'Full Video'}</strong></span>
                    <span class="gallery-meta-tag gallery-resolution-tag" style="font-size: 11px; padding: 2px 7px;" title="Neural DiT Resolution">🎯 <strong>${escapeHtml(v.resolution_label || (v.resolution ? v.resolution.toUpperCase() + ' DiT' : '500p DiT'))}</strong></span>
                    <span class="gallery-meta-tag gallery-tag-720p" style="font-size: 11px; padding: 2px 7px;" title="Render Time Taken">⚡ <strong>${formatRenderTimeDisplay(v.render_time_label || v.render_time)}</strong></span>
                    <span class="gallery-meta-tag" style="font-size: 11px; padding: 2px 7px; background: #f1f5f9; color: #475569;" title="File Size">💾 <strong>${s1080} MB</strong></span>
                  </div>

                  <!-- Embedded Video Player Preview -->
                  <div style="position: relative; width: 100%; border-radius: var(--radius-md); overflow: hidden; background: #000000; margin-bottom: 12px; aspect-ratio: 16/9; max-height: 200px; display: flex; justify-content: center; align-items: center;">
                    <video controls preload="metadata" playsinline style="width: 100%; height: 100%; object-fit: contain;" src="${safeUrl1080}">
                      Your browser does not support HTML5 video preview.
                    </video>
                  </div>
                </div>

                <!-- Full-Width Dual Green/Emerald Download Buttons Stack -->
                <div class="gallery-card-download-stack" style="margin-top: 6px;" onclick="event.stopPropagation();">
                  <a href="${dlUrl720}" download="${escapeHtml(safeFn720)}" data-url="${dlUrl720}" data-filename="${escapeHtml(safeFn720)}" class="btn-card-dl-btn btn-dl-720p" title="Download 720P Fast Preview (${s720} MB)" onclick="handleTurboDownloadClick(this, event);">
                    <div class="dl-btn-content">
                      <span class="dl-icon">⚡</span>
                      <span class="dl-text">Download 720P HD</span>
                    </div>
                    <span class="dl-size-badge">${s720} MB</span>
                  </a>

                  <a href="${dlUrl1080}" download="${escapeHtml(safeFn1080)}" data-url="${dlUrl1080}" data-filename="${escapeHtml(safeFn1080)}" class="btn-card-dl-btn btn-dl-1080p" title="Download 1080P Ultra-HD Master (${s1080} MB)" onclick="handleTurboDownloadClick(this, event);">
                    <div class="dl-btn-content">
                      <span class="dl-icon">🎬</span>
                      <span class="dl-text">Download 1080P Full HD</span>
                    </div>
                    <span class="dl-size-badge">${s1080} MB</span>
                  </a>
                </div>

              </div>
            `;
          }).join('')}
        </div>
      ` : `
        <div style="padding: 20px; background: #f8fafc; border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); text-align: center; color: var(--text-muted); font-size: 13px;">
          No completed videos in queue history yet.
        </div>
      `}
    </div>
  `;
}

async function handleTurboDownloadClick(btn, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  if (!btn || btn._downloading) return;

  const targetUrl = btn.dataset.url || btn.getAttribute('href') || '';
  const targetFilename = btn.dataset.filename || btn.getAttribute('download') || 'video.mp4';
  if (!targetUrl) return;

  btn._downloading = true;
  const textEl = btn.querySelector('.dl-text');
  const sizeBadge = btn.querySelector('.dl-size-badge');
  const origHtml = textEl ? textEl.innerHTML : '';
  const origBadge = sizeBadge ? sizeBadge.innerHTML : '';

  const updateProgress = (pct, speedStr) => {
    if (textEl) textEl.innerHTML = `⚡ <strong>${pct}%</strong> <span style="font-size:11px;opacity:0.85;">(${speedStr})</span>`;
  };

  try {
    if (textEl) textEl.innerHTML = '⚡ <strong>Connecting...</strong>';

    // 1. First probe Content-Length using HEAD or small Range request
    let totalBytes = 0;
    try {
      const probeRes = await fetch(targetUrl, { method: 'HEAD' });
      totalBytes = parseInt(probeRes.headers.get('content-length') || '0', 10);
    } catch (e) {}

    if (!totalBytes || totalBytes < 5 * 1024 * 1024) {
      // Small file or HEAD failed -> Direct browser download
      fallbackDirectDownload(targetUrl, targetFilename);
      btn._downloading = false;
      if (textEl) textEl.innerHTML = origHtml;
      return;
    }

    // 2. High-speed multi-threaded range worker download (24 concurrent streams)
    // Cloudflare limits single stream to ~60-120 KB/s, but 24 parallel streams achieve 15-30 MB/s!
    const numWorkers = Math.min(24, Math.max(8, Math.ceil(totalBytes / (8 * 1024 * 1024))));
    const chunkSize = Math.ceil(totalBytes / numWorkers);
    const chunks = new Array(numWorkers);
    let downloadedBytes = 0;
    const startTime = Date.now();

    const fetchWorker = async (index) => {
      const start = index * chunkSize;
      const end = Math.min(totalBytes - 1, (index + 1) * chunkSize - 1);
      if (start > end) {
        chunks[index] = new Uint8Array(0);
        return;
      }

      const res = await fetch(targetUrl, {
        headers: { 'Range': `bytes=${start}-${end}` }
      });

      if (!res.ok && res.status !== 206) {
        throw new Error(`Range request failed with status ${res.status}`);
      }

      const reader = res.body.getReader();
      const partLength = end - start + 1;
      const partBuffer = new Uint8Array(partLength);
      let partOffset = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        partBuffer.set(value, partOffset);
        partOffset += value.length;
        downloadedBytes += value.length;

        const elapsedSec = Math.max(0.2, (Date.now() - startTime) / 1000);
        const speedMb = (downloadedBytes / (1024 * 1024)) / elapsedSec;
        const pct = Math.min(99, Math.round((downloadedBytes / totalBytes) * 100));
        updateProgress(pct, `${speedMb.toFixed(1)} MB/s`);
      }

      chunks[index] = partBuffer;
    };

    // Run all workers concurrently
    await Promise.all(Array.from({ length: numWorkers }, (_, i) => fetchWorker(i)));

    if (textEl) textEl.innerHTML = '✅ <strong>Saving Video...</strong>';

    const finalBlob = new Blob(chunks, { type: 'video/mp4' });
    const blobUrl = URL.createObjectURL(finalBlob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = targetFilename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      try { document.body.removeChild(a); } catch (e) {}
      URL.revokeObjectURL(blobUrl);
    }, 15000);

    if (textEl) textEl.innerHTML = '🎉 <strong>Downloaded!</strong>';
    setTimeout(() => {
      if (textEl) textEl.innerHTML = origHtml;
      btn._downloading = false;
    }, 3000);

  } catch (err) {
    console.warn('Parallel download error, falling back to direct download:', err);
    fallbackDirectDownload(targetUrl, targetFilename);
    if (textEl) textEl.innerHTML = origHtml;
    btn._downloading = false;
  }
}

function fallbackDirectDownload(url, filename) {
  const cleanUrl = url.includes('?') ? `${url}&download=1` : `${url}?download=1`;
  const a = document.createElement('a');
  a.href = cleanUrl;
  a.download = filename || 'video.mp4';
  a.target = '_blank';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    try { document.body.removeChild(a); } catch (e) {}
  }, 2000);
}

// ==========================================
// 8. Video Player & Modals
// ==========================================
function formatRenderTimeDisplay(input) {
  if (!input) return '0s';
  const str = String(input).trim();
  if (!str) return '0s';

  // If already formatted (e.g. '8m 22s', '18m 20s', '3h 59m', '4m 2s', '32s', '2 hrs 11 min')
  if (/[0-9]+[smh]/i.test(str) || str.includes('min') || str.includes('hr') || str.includes('sec')) {
    return str;
  }

  const val = parseFloat(str);
  if (!isNaN(val) && val > 0) {
    return formatHumanDuration(val);
  }

  return str;
}

function applyVideoPlayerAspect(videoPlayer, forcedRatio = null) {
  const container = document.querySelector('.video-player-container');
  if (!container) return;

  let targetClass = 'ratio-9-16';

  // Ground truth 1: If video metadata is already loaded and dimensions are known
  if (videoPlayer && videoPlayer.videoWidth > 0 && videoPlayer.videoHeight > 0) {
    const aspect = videoPlayer.videoWidth / videoPlayer.videoHeight;
    if (aspect < 0.78) {
      targetClass = 'ratio-9-16';
    } else if (aspect > 1.25) {
      targetClass = 'ratio-16-9';
    } else if (Math.abs(aspect - 1.0) <= 0.15) {
      targetClass = 'ratio-1-1';
    } else {
      targetClass = 'ratio-4-5';
    }
  } else {
    // Ground truth 2: Explicit ratio passed or slot detected ratio
    let targetRatio = forcedRatio;
    if (!targetRatio || targetRatio === 'auto') {
      const activeSlot = getActiveSlot();
      if (activeSlot) {
        targetRatio = activeSlot.detectedRatio || (activeSlot.selectedRatio !== 'auto' ? activeSlot.selectedRatio : null);
      }
    }

    if (targetRatio === '16:9' || targetRatio === 'landscape') {
      targetClass = 'ratio-16-9';
    } else if (targetRatio === '1:1' || targetRatio === 'square') {
      targetClass = 'ratio-1-1';
    } else if (targetRatio === '4:5') {
      targetClass = 'ratio-4-5';
    } else {
      targetClass = 'ratio-9-16';
    }
  }

  // Prevent layout thrashing: only update classList if targetClass is not already set
  if (!container.classList.contains(targetClass)) {
    container.classList.remove('ratio-9-16', 'ratio-16-9', 'ratio-1-1', 'ratio-4-5');
    container.classList.add(targetClass);
  }
}

function loadRenderedVideo(videoUrl, filename, sizeMb, autoplay = false, slotName = null, duration = null, genTime = null, url720p = null, filename720p = null, size720pMb = null) {
  const activeSlot = getActiveSlot();
  const currentName = slotName || (activeSlot ? activeSlot.name : 'Video');
  const titleEl = $('renderedVideoCardTitle');
  const videoPlayer = $('mainVideoPlayer');
  const overlay = $('videoPlaceholderOverlay');
  const filenameEl = $('renderedVideoFilename');
  const btnDownload1080p = $('btnDownloadVideo1080p');
  const btnDownload720p = $('btnDownloadVideo720p');
  const btnFullscreen = $('btnFullscreenPreview');

  const safeUrl1080 = videoUrl ? encodeURI(decodeURI(videoUrl)) : '';
  const safeUrl720p = url720p ? encodeURI(decodeURI(url720p)) : '';
  const streamTarget = safeUrl720p || safeUrl1080;
  const posterTarget = (safeUrl1080 ? safeUrl1080.replace('.mp4', '.jpg') : '') || (safeUrl720p ? safeUrl720p.replace('_720p.mp4', '.jpg').replace('.mp4', '.jpg') : '');

  if (titleEl) {
    titleEl.innerHTML = `🎬 Output Video: <strong style="color: var(--blue-primary);">${escapeHtml(currentName)}</strong>`;
  }

  if (videoPlayer && streamTarget) {
    if (posterTarget) videoPlayer.poster = posterTarget;
    const isAlreadyLoaded = (videoPlayer.dataset.loadedSrc === streamTarget);
    if (!isAlreadyLoaded) {
      videoPlayer.dataset.loadedSrc = streamTarget;
      videoPlayer.pause();
      videoPlayer.removeAttribute('src');
      videoPlayer.src = streamTarget;
      videoPlayer.innerHTML = `<source src="${streamTarget}" type="video/mp4">`;
      videoPlayer.load();

      const onFrameReady = () => {
        try {
          if (videoPlayer.paused && videoPlayer.currentTime === 0) {
            videoPlayer.currentTime = 0.01;
          }
        } catch (e) {}
      };
      videoPlayer.addEventListener('loadeddata', onFrameReady, { once: true });
      videoPlayer.addEventListener('loadedmetadata', onFrameReady, { once: true });

      if (autoplay) {
        videoPlayer.muted = true;
        videoPlayer.play().catch(() => {
          onFrameReady();
        });
      }

      const activeRatio = activeSlot ? (activeSlot.detectedRatio || activeSlot.selectedRatio) : null;
      applyVideoPlayerAspect(videoPlayer, activeRatio);

      videoPlayer.onloadedmetadata = () => applyVideoPlayerAspect(videoPlayer);
      videoPlayer.onloadeddata = () => applyVideoPlayerAspect(videoPlayer);
      videoPlayer.oncanplay = () => applyVideoPlayerAspect(videoPlayer);
      videoPlayer.onplay = () => applyVideoPlayerAspect(videoPlayer);
    }

    if (overlay) {
      overlay.classList.add('hidden');
      overlay.style.display = 'none';
    }

    let metaPieces = [];
    if (duration) metaPieces.push(`⏱️ ${escapeHtml(duration)}`);
    if (sizeMb || size720pMb) metaPieces.push(`💾 ${sizeMb ? `${sizeMb} MB` : `${size720pMb} MB`}`);
    if (genTime) metaPieces.push(`⚡ ${escapeHtml(formatRenderTimeDisplay(genTime))}`);

    if (filenameEl) {
      filenameEl.innerHTML = `
        <div class="rendered-meta-title">🎬 <strong>${escapeHtml(currentName)}</strong> — <span class="rendered-meta-filename">${escapeHtml(filename || 'video.mp4')}</span></div>
        ${metaPieces.length > 0 ? `<div class="rendered-meta-stats">${metaPieces.map(m => `<span class="rendered-meta-pill">${m}</span>`).join('')}</div>` : ''}
      `;
    }

    // 1080P Download Button
    if (btnDownload1080p) {
      const fn1080 = filename || `${currentName.toLowerCase().replace(/\s+/g, '_')}_1080p.mp4`;
      const dlUrl1080 = safeUrl1080.includes('?') ? `${safeUrl1080}&download=1` : `${safeUrl1080}?download=1`;
      btnDownload1080p.href = dlUrl1080;
      btnDownload1080p.download = fn1080;
      btnDownload1080p.dataset.url = dlUrl1080;
      btnDownload1080p.dataset.filename = fn1080;
      btnDownload1080p.onclick = (e) => handleTurboDownloadClick(btnDownload1080p, e);
      btnDownload1080p.classList.remove('disabled');
      const textSpan = $('btnDownload1080pText');
      if (textSpan) textSpan.innerHTML = `📥 1080P (${sizeMb ? `${sizeMb} MB` : 'Master'})`;
    }

    // 720P Download Button
    if (btnDownload720p) {
      const fn720 = filename720p || (filename ? filename.replace('.mp4', '_720p.mp4') : `${currentName.toLowerCase().replace(/\s+/g, '_')}_720p.mp4`);
      const dlUrl720 = safeUrl720p.includes('?') ? `${safeUrl720p}&download=1` : `${safeUrl720p}?download=1`;
      btnDownload720p.href = dlUrl720;
      btnDownload720p.download = fn720;
      btnDownload720p.dataset.url = dlUrl720;
      btnDownload720p.dataset.filename = fn720;
      btnDownload720p.onclick = (e) => handleTurboDownloadClick(btnDownload720p, e);
      btnDownload720p.classList.remove('disabled');
      const textSpan720 = $('btnDownload720pText');
      if (textSpan720) textSpan720.innerHTML = `⚡ 720P (${size720pMb ? `${size720pMb} MB` : 'Fast'})`;
    }

    if (btnFullscreen) {
      btnFullscreen.disabled = false;
      btnFullscreen.onclick = () => openFullscreenModal(safeUrl1080, filename, safeUrl720p, filename720p, sizeMb, size720pMb);
    }
  }
}

function resetVideoPlayerUI(slotName = null) {
  const activeSlot = getActiveSlot();
  const currentName = slotName || (activeSlot ? activeSlot.name : 'Active Tab');
  const titleEl = $('renderedVideoCardTitle');
  const videoPlayer = $('mainVideoPlayer');
  const overlay = $('videoPlaceholderOverlay');
  const filenameEl = $('renderedVideoFilename');
  const btnDownload1080p = $('btnDownloadVideo1080p');
  const btnDownload720p = $('btnDownloadVideo720p');
  const btnFullscreen = $('btnFullscreenPreview');

  if (titleEl) {
    titleEl.innerHTML = `Rendered Video: <span>${escapeHtml(currentName)}</span>`;
  }

  if (videoPlayer) {
    videoPlayer.pause();
    videoPlayer.removeAttribute('src');
    videoPlayer.src = '';
  }
  if (overlay) {
    overlay.classList.remove('hidden');
    overlay.style.display = 'flex';
    const span = overlay.querySelector('span');
    if (span) span.textContent = `Rendered video for ${currentName} will play here`;
  }
  if (filenameEl) filenameEl.innerHTML = `<span style="color: var(--text-muted);">No video rendered yet for ${escapeHtml(currentName)}</span>`;
  if (btnDownload1080p) btnDownload1080p.classList.add('disabled');
  if (btnDownload720p) btnDownload720p.classList.add('disabled');
  if (btnFullscreen) btnFullscreen.disabled = true;

  const activeRatio = activeSlot ? (activeSlot.detectedRatio || activeSlot.selectedRatio) : '9:16';
  applyVideoPlayerAspect(videoPlayer, activeRatio);
}

function initModals() {
  const modal = $('fullscreenModal');
  const closeBtn = $('modalCloseBtn');
  const qCloseBtn = $('queueModalCloseBtn');
  const qModal = $('queueMonitorModal');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      const vid = $('modalVideoPlayer');
      if (vid) vid.pause();
      modal.classList.add('hidden');
    });
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        const vid = $('modalVideoPlayer');
        if (vid) vid.pause();
        modal.classList.add('hidden');
      }
    });
  }

  if (qCloseBtn && qModal) {
    qCloseBtn.addEventListener('click', () => {
      qModal.classList.add('hidden');
    });
  }

  if (qModal) {
    qModal.addEventListener('click', (e) => {
      if (e.target === qModal) {
        qModal.classList.add('hidden');
      }
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const vid = $('modalVideoPlayer');
      if (vid) vid.pause();
      if (modal && !modal.classList.contains('hidden')) {
        modal.classList.add('hidden');
      } else if (qModal && !qModal.classList.contains('hidden')) {
        qModal.classList.add('hidden');
      } else {
        closeAudioLibraryModal();
      }
    }
  });

  initAudioLibraryModal();
}

// ==========================================
// Persistent Audio Library Management
// Zero-Upload Instant Audio Attachment
// ==========================================

let activeLibraryAudioPlayer = null;
let currentPlayingAudioId = null;
let audioLibraryData = [];
let audioUploadQueue = [];
let isAudioUploading = false;
let currentUploadSessionId = 0;
let currentUploadXhr = null;
let currentUploadingItem = null;

function initAudioLibraryModal() {
  const btnOpen = $('btnOpenAudioLibrary');
  const modal = $('audioLibraryModal');
  const btnClose = $('audioLibraryModalCloseBtn');
  const btnRefresh = $('btnRefreshAudioLibrary');
  const searchInput = $('audioLibrarySearch');

  if (btnOpen && modal) {
    btnOpen.addEventListener('click', () => {
      modal.classList.remove('hidden');
      fetchAndRenderAudioLibrary();
    });
  }

  if (btnClose && modal) {
    btnClose.addEventListener('click', closeAudioLibraryModal);
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeAudioLibraryModal();
    });
  }

  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      fetchAndRenderAudioLibrary(true);
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      renderAudioLibraryList(searchInput.value.trim().toLowerCase());
    });
  }

  const btnCancelAll = $('btnCancelAllAudioLibrary');
  if (btnCancelAll) {
    btnCancelAll.addEventListener('click', async () => {
      const inFlightItems = audioLibraryData.filter(item => item.upload_status === 'uploading' || item.upload_status === 'waiting');
      if (inFlightItems.length === 0 && audioUploadQueue.length === 0 && !isAudioUploading) {
        showNotification('ℹ️ বর্তমানে কোনো অডিও আপলোড চলমান বা কিউতে অপেক্ষমান নেই।');
        return;
      }

      const totalCount = inFlightItems.length || audioUploadQueue.length;
      const confirmed = confirm(`⚠️ আপনি কি চলমান ও কিউতে থাকা সকল (${totalCount}টি) অডিও আপলোড বাতিল করতে চান?\n\n(নোট: ইতিমধ্যে সফলভাবে আপলোড হওয়া অডিও ফাইলগুলো লাইব্রেরিতে অক্ষত থাকবে)`);
      if (!confirmed) return;

      const origText = btnCancelAll.innerHTML;
      btnCancelAll.disabled = true;
      btnCancelAll.innerHTML = '⏳ বাতিল হচ্ছে...';

      // 1. Invalidate current upload session to kill any async processing
      currentUploadSessionId++;

      // 2. Abort active upload XHR immediately
      if (currentUploadXhr) {
        try {
          currentUploadXhr.abort();
        } catch (e) {}
        currentUploadXhr = null;
      }
      currentUploadingItem = null;

      // 3. Clear the queue
      const inFlightFilenames = inFlightItems.map(item => item.filename);
      audioUploadQueue = [];
      isAudioUploading = false;

      // 4. Restore the upload button
      const btnUpload = $('btnUploadToAudioLibrary');
      if (btnUpload) {
        btnUpload.disabled = false;
        btnUpload.innerHTML = '⬆️ অডিও আপলোড';
      }

      // 5. Remove uploading and waiting items from UI data list (keep uploaded ones!)
      audioLibraryData = audioLibraryData.filter(item => item.upload_status !== 'uploading' && item.upload_status !== 'waiting');
      renderAudioLibraryList();

      // 6. Tell server backend to cancel any partial upload streams and delete .tmp files
      try {
        await fetch('/api/audio_library/cancel_all', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filenames: inFlightFilenames })
        });
      } catch (e) {
        console.warn('cancel_all error:', e);
      } finally {
        btnCancelAll.disabled = false;
        btnCancelAll.innerHTML = origText;
      }

      showNotification(`⏹️ চলমান ও কিউতে থাকা সকল (${totalCount}টি) অডিও আপলোড সফলভাবে বাতিল করা হয়েছে।`);
    });
  }

  const btnDeleteAll = $('btnDeleteAllAudioLibrary');
  if (btnDeleteAll) {
    btnDeleteAll.addEventListener('click', async () => {
      if (audioLibraryData.length === 0) {
        showNotification('ℹ️ লাইব্রেরিতে ডিলিট করার মতো কোনো অডিও ফাইল নেই।');
        return;
      }
      const confirmed = confirm(`⚠️ আপনি কি অডিও লাইব্রেরির সকল (${audioLibraryData.length} টি) অডিও ফাইল স্থায়ীভাবে ডিলিট করে সার্ভারের ডিস্ক স্পেস সম্পূর্ণ খালি করতে চান?\n\nএই কাজ সম্পন্ন হলে অডিও ফাইলগুলো পারমানেন্টলি মুছে যাবে।`);
      if (!confirmed) return;

      // Abort any ongoing upload immediately & clear queue
      currentUploadSessionId++;
      if (currentUploadXhr) {
        try {
          currentUploadXhr.abort();
        } catch (e) {}
        currentUploadXhr = null;
      }
      currentUploadingItem = null;
      audioUploadQueue = [];
      isAudioUploading = false;
      const btnUpload = $('btnUploadToAudioLibrary');
      if (btnUpload) {
        btnUpload.disabled = false;
        btnUpload.innerHTML = '⬆️ অডিও আপলোড';
      }

      const origText = btnDeleteAll.innerHTML;
      btnDeleteAll.disabled = true;
      btnDeleteAll.innerHTML = '⏳ ডিলিট হচ্ছে...';

      try {
        const res = await fetch('/api/audio_library/delete_all', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ all: true })
        });
        const json = await res.json();
        if (json.success) {
          stopLibraryAudioPreview();
          audioLibraryData = [];
          showNotification(`🗑️ ${json.count || 0}টি অডিও ফাইল স্থায়ীভাবে মুছে ফেলা হয়েছে এবং ডিস্ক খালি করা হয়েছে!`);
          renderAudioLibraryList();
        } else {
          alert('Delete all failed: ' + (json.error || 'অজানা সমস্যা'));
        }
      } catch (err) {
        alert('Delete all error: ' + err.message);
      } finally {
        btnDeleteAll.disabled = false;
        btnDeleteAll.innerHTML = origText;
      }
    });
  }

  const btnUpload = $('btnUploadToAudioLibrary');
  const uploadInput = $('audioLibraryUploadInput');
  if (btnUpload && uploadInput) {
    btnUpload.addEventListener('click', () => {
      uploadInput.value = '';
      uploadInput.click();
    });

    uploadInput.addEventListener('change', () => {
      const files = Array.from(uploadInput.files || []);
      if (files.length === 0) return;

      const allowedExts = ['.wav', '.mp3', '.m4a', '.aac', '.ogg', '.flac'];
      const validFiles = files.filter(f => {
        const ext = '.' + f.name.split('.').pop().toLowerCase();
        return allowedExts.includes(ext) || f.type.startsWith('audio/');
      });

      if (validFiles.length === 0) {
        showNotification('⚠️ অনুগ্রহ করে সঠিক অডিও ফাইল (.wav, .mp3, .m4a, .aac, .ogg, .flac) নির্বাচন করুন।');
        return;
      }

      // Build queue items for all selected files
      const newQueueItems = validFiles.map(file => {
        const tempId = 'upl_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        return {
          id: tempId,
          filename: file.name,
          duration: 0,
          duration_formatted: '--:--',
          size_mb: sizeMb,
          size_bytes: file.size,
          url: '',
          is_uploaded: false,
          upload_status: 'waiting',
          progress: 0,
          file: file
        };
      });

      // Filter out duplicates if already in list
      const existingNames = new Set(newQueueItems.map(q => q.filename));
      audioLibraryData = [...newQueueItems, ...audioLibraryData.filter(item => !existingNames.has(item.filename))];

      // Add to sequential upload queue
      audioUploadQueue.push(...newQueueItems);

      // Render immediately so all selected files appear instantly in their preview rows!
      renderAudioLibraryList();

      showNotification(`📋 ${validFiles.length}টি অডিও কিউতে যোগ করা হয়েছে। ক্রমান্বয়ে আপলোড শুরু হচ্ছে...`);

      // Trigger sequential queue processing
      processAudioUploadQueue();
    });
  }
}

async function processAudioUploadQueue() {
  if (isAudioUploading) return;
  if (audioUploadQueue.length === 0) {
    const btnUpload = $('btnUploadToAudioLibrary');
    if (btnUpload) {
      btnUpload.disabled = false;
      btnUpload.innerHTML = '⬆️ অডিও আপলোড';
    }
    return;
  }

  isAudioUploading = true;
  const currentItem = audioUploadQueue[0];
  const thisSessionId = ++currentUploadSessionId;
  currentUploadingItem = currentItem;
  currentItem.upload_status = 'uploading';
  currentItem.progress = 0;

  const btnUpload = $('btnUploadToAudioLibrary');
  if (btnUpload) {
    btnUpload.disabled = true;
    btnUpload.innerHTML = `⏳ আপলোড হচ্ছে (${audioUploadQueue.length} বাকি)...`;
  }

  renderAudioLibraryList();

  try {
    await uploadSingleAudioFile(currentItem);
    if (currentUploadSessionId === thisSessionId) {
      currentItem.upload_status = 'uploaded';
      currentItem.is_uploaded = true;
      showNotification(`✅ '${currentItem.filename}' সফলভাবে লাইব্রেরিতে আপলোড হয়েছে!`);
    }
  } catch (err) {
    if (currentUploadSessionId === thisSessionId) {
      if (err && err.name === 'AbortError') {
        console.log(`Audio upload aborted for ${currentItem.filename}`);
      } else {
        console.error(`Audio upload failed for ${currentItem.filename}:`, err);
        currentItem.upload_status = 'error';
        currentItem.errorMessage = err.message || 'আপলোড ব্যর্থ';
        showNotification(`❌ '${currentItem.filename}' আপলোড ত্রুটি: ${err.message}`);
      }
    }
  } finally {
    if (currentUploadSessionId === thisSessionId) {
      if (audioUploadQueue.length > 0 && audioUploadQueue[0] === currentItem) {
        audioUploadQueue.shift();
      }
      currentUploadXhr = null;
      currentUploadingItem = null;
      isAudioUploading = false;
      renderAudioLibraryList();

      if (audioUploadQueue.length > 0) {
        setTimeout(() => {
          processAudioUploadQueue();
        }, 50);
      } else {
        if (btnUpload) {
          btnUpload.disabled = false;
          btnUpload.innerHTML = '⬆️ অডিও আপলোড';
        }
        showNotification('🎉 সকল নির্বাচিত অডিও আপলোড সম্পন্ন হয়েছে!');
        await fetchAndRenderAudioLibrary(false);
      }
    }
  }
}

function uploadSingleAudioFile(item) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    currentUploadXhr = xhr;

    xhr.open('POST', `/api/audio_library/upload?filename=${encodeURIComponent(item.filename)}`, true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && e.total > 0) {
        const pct = Math.round((e.loaded / e.total) * 100);
        item.progress = pct;
        const progressEl = document.getElementById(`audio-progress-${item.id}`);
        if (progressEl) {
          progressEl.textContent = `${pct}%`;
        }
      }
    };

    xhr.onload = () => {
      currentUploadXhr = null;
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          if (res.success) {
            item.filename = res.filename || item.filename;
            item.url = res.url || `/audio_library/${encodeURIComponent(item.filename)}`;
            item.duration = res.duration || item.duration || 0;
            item.duration_formatted = res.duration_formatted || item.duration_formatted || '--:--';
            item.size_mb = res.size_mb || item.size_mb;
            item.id = res.id || item.id;
            item.is_uploaded = true;
            resolve(res);
          } else {
            reject(new Error(res.error || 'সার্ভার সমস্যা'));
          }
        } catch (e) {
          reject(new Error('অকার্যকর সার্ভার রেসপন্স'));
        }
      } else {
        reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText || 'আপলোড ব্যর্থ'}`));
      }
    };

    xhr.onerror = () => {
      currentUploadXhr = null;
      reject(new Error('নেটওয়ার্ক সংযোগ বিচ্ছিন্ন'));
    };

    xhr.onabort = () => {
      currentUploadXhr = null;
      const abortErr = new Error('আপলোড বাতিল করা হয়েছে');
      abortErr.name = 'AbortError';
      reject(abortErr);
    };

    xhr.ontimeout = () => {
      currentUploadXhr = null;
      reject(new Error('আপলোড সময়সীমা উত্তীর্ণ হয়েছে'));
    };

    xhr.timeout = 30 * 60 * 1000;
    xhr.send(item.file);
  });
}

function closeAudioLibraryModal() {
  const modal = $('audioLibraryModal');
  if (modal) modal.classList.add('hidden');
  stopLibraryAudioPreview();
}

function stopLibraryAudioPreview() {
  if (activeLibraryAudioPlayer) {
    try {
      activeLibraryAudioPlayer.pause();
      activeLibraryAudioPlayer = null;
    } catch (e) {}
  }
  currentPlayingAudioId = null;
  $$('.library-play-btn').forEach(b => {
    b.innerHTML = '▶';
    b.classList.remove('playing');
  });
}

async function fetchAndRenderAudioLibrary(isManualRefresh = false) {
  const bodyEl = $('audioLibraryBody');
  if (!bodyEl) return;

  const inFlightItems = audioLibraryData.filter(item => item.upload_status === 'uploading' || item.upload_status === 'waiting');
  const inFlightFilenames = new Set(inFlightItems.map(p => p.filename));

  if ((isManualRefresh || audioLibraryData.length === 0) && inFlightItems.length === 0) {
    bodyEl.innerHTML = `
      <div style="text-align: center; padding: 30px; color: var(--text-muted);">
        <span class="badge-icon-spin" style="font-size: 24px; display: block; margin-bottom: 10px;">🔄</span>
        লাইব্রেরি অডিও লোড হচ্ছে...
      </div>
    `;
  }

  try {
    const [res, compRes] = await Promise.all([
      fetch('/api/audio_library'),
      fetch('/audio_library/completed_audios.json?t=' + Date.now()).catch(() => null)
    ]);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    let completedMap = {};
    if (compRes && compRes.ok) {
      try {
        completedMap = await compRes.json();
      } catch (e) {
        completedMap = {};
      }
    }
    const serverAudios = Array.isArray(data.audios) ? data.audios.map(item => ({
      ...item,
      is_uploaded: Boolean(item.is_uploaded || completedMap[item.filename]),
      upload_status: 'uploaded'
    })) : [];

    const dedupedServer = serverAudios.filter(s => !inFlightFilenames.has(s.filename));
    audioLibraryData = [...inFlightItems, ...dedupedServer];
    renderAudioLibraryList();
  } catch (err) {
    console.error('Audio library fetch error:', err);
    if (inFlightItems.length === 0) {
      bodyEl.innerHTML = `
        <div style="text-align: center; padding: 25px; color: #ef4444; background: rgba(239, 68, 68, 0.1); border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.2);">
          ⚠️ অডিও লাইব্রেরি লোড করতে সমস্যা হয়েছে: ${err.message}<br>
          <button onclick="fetchAndRenderAudioLibrary(true)" style="margin-top: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 5px 12px; border-radius: 6px; cursor: pointer;">পুনরায় চেষ্টা করুন</button>
        </div>
      `;
    }
  }
}

function renderAudioLibraryList(filterText = '') {
  const bodyEl = $('audioLibraryBody');
  if (!bodyEl) return;

  const btnCancelAll = $('btnCancelAllAudioLibrary');
  if (btnCancelAll) {
    const hasInFlight = audioLibraryData.some(a => a.upload_status === 'uploading' || a.upload_status === 'waiting') || audioUploadQueue.length > 0;
    if (hasInFlight) {
      btnCancelAll.style.opacity = '1';
      btnCancelAll.style.cursor = 'pointer';
      btnCancelAll.title = 'চলমান ও কিউতে থাকা সকল আপলোড বাতিল করুন';
    } else {
      btnCancelAll.style.opacity = '0.55';
      btnCancelAll.style.cursor = 'default';
      btnCancelAll.title = 'কোনো আপলোড চলমান নেই';
    }
  }

  let filtered = audioLibraryData;
  if (filterText) {
    filtered = audioLibraryData.filter(a => (a.filename || '').toLowerCase().includes(filterText));
  }

  if (filtered.length === 0) {
    if (audioLibraryData.length === 0) {
      bodyEl.innerHTML = `
        <div style="text-align: center; padding: 35px 20px; background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 14px;">
          <div style="font-size: 32px; margin-bottom: 10px;">📂</div>
          <h4 style="color: #fff; margin: 0 0 6px 0; font-size: 15px;">লাইব্রেরিতে কোনো অডিও ফাইল পাওয়া যায়নি</h4>
          <p style="color: var(--text-muted); font-size: 12.5px; max-width: 440px; margin: 0 auto; line-height: 1.5;">
            উপরে <strong>⬆️ অডিও আপলোড</strong> বাটনে ক্লিক করে ফাইল আপলোড করুন, অথবা ম্যাকবুকের <code>audio_library/</code> ফোল্ডারে অডিও ফাইল কপি করে <code>./sync_audio.sh</code> রান করুন।
          </p>
        </div>
      `;
    } else {
      bodyEl.innerHTML = `
        <div style="text-align: center; padding: 25px; color: var(--text-muted); font-size: 13px;">
          '${filterText}' নামের কোনো অডিও পাওয়া যায়নি।
        </div>
      `;
    }
    return;
  }

  const activeSlot = getActiveSlot();
  const currentSlotName = activeSlot ? activeSlot.name : 'Active Video';

  bodyEl.innerHTML = filtered.map(item => {
    const isPlaying = currentPlayingAudioId === item.id;
    const isSelected = activeSlot && activeSlot.audioLibraryFilename === item.filename;
    const status = item.upload_status || (item.is_uploaded ? 'uploaded' : 'uploaded');

    let statusBadgeHtml = '';
    let actionBtnHtml = '';
    let isPlayDisabled = false;

    if (status === 'uploading') {
      isPlayDisabled = true;
      statusBadgeHtml = `
        <span class="audio-status-pill uploading" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 10px; letter-spacing: 0.3px; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px;">
          <span class="mini-pulse-dot" style="background: #fbbf24; width: 6px; height: 6px; border-radius: 50%; display: inline-block;"></span>
          Uploading... <span id="audio-progress-${item.id}" style="margin-left: 2px; font-weight: 800; color: #fef08a;">${item.progress || 0}%</span>
        </span>
      `;
      actionBtnHtml = `
        <button type="button" disabled style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: not-allowed; white-space: nowrap; display: inline-flex; align-items: center; gap: 6px;">
          <span style="display:inline-block; width:10px; height:10px; border:2px solid #fbbf24; border-top-color:transparent; border-radius:50%; animation:spin 1s linear infinite;"></span>
          আপলোড হচ্ছে...
        </button>
      `;
    } else if (status === 'waiting') {
      isPlayDisabled = true;
      statusBadgeHtml = `
        <span class="audio-status-pill waiting" style="background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.35); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 10px; letter-spacing: 0.3px; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px;">
          ⏳ Waiting...
        </span>
      `;
      actionBtnHtml = `
        <button type="button" disabled style="background: rgba(255,255,255,0.06); color: #94a3b8; border: 1px solid rgba(255,255,255,0.1); padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: not-allowed; white-space: nowrap;">
          ⏳ ওয়েটিং...
        </button>
      `;
    } else if (status === 'error') {
      statusBadgeHtml = `
        <span class="audio-status-pill error" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 10px; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px;">
          ❌ ত্রুটি
        </span>
      `;
      actionBtnHtml = `
        <button type="button" class="btn-retry-library-audio" data-id="${item.id}" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; padding: 7px 12px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; white-space: nowrap;">
          🔄 Retry
        </button>
      `;
    } else {
      statusBadgeHtml = `
        <span class="audio-status-pill uploaded" style="background: #ffffff; color: #000000; padding: 2px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; letter-spacing: 0.4px; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.35);">✓ Uploaded</span>
      `;
      actionBtnHtml = `
        <button type="button" class="btn-select-library-audio" data-filename="${item.filename}" data-duration="${item.duration}" data-sizemb="${item.size_mb}" data-url="${item.url}" data-id="${item.id}" style="background: ${isSelected ? 'rgba(16, 185, 129, 0.3)' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)'}; color: #ffffff; border: 1px solid ${isSelected ? '#10b981' : 'rgba(255,255,255,0.2)'}; padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);">
          ${isSelected ? '✓ Selected' : `👉 Use for ${currentSlotName}`}
        </button>
      `;
    }

    return `
      <div class="audio-lib-item" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: ${isSelected ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.04)'}; border: 1px solid ${isSelected ? 'rgba(16, 185, 129, 0.5)' : 'rgba(255, 255, 255, 0.08)'}; border-radius: 12px; gap: 12px; transition: all 0.2s ease;">
        <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
          <button type="button" class="library-play-btn ${isPlaying ? 'playing' : ''}" data-url="${item.url}" data-id="${item.id}" ${isPlayDisabled ? 'disabled style="width: 36px; height: 36px; border-radius: 50%; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #64748b; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: not-allowed; flex-shrink: 0;"' : 'style="width: 36px; height: 36px; border-radius: 50%; background: ' + (isPlaying ? '#10b981' : 'rgba(255,255,255,0.1)') + '; border: 1px solid rgba(255,255,255,0.2); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; flex-shrink: 0; transition: all 0.2s ease;"'}>
            ${isPlaying ? '⏸' : '▶'}
          </button>
          <div style="flex: 1; min-width: 0;">
            <div style="color: #ffffff; font-weight: 700; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${item.filename}">
              ${item.filename}
            </div>
            <div style="display: flex; gap: 8px; align-items: center; margin-top: 5px; font-size: 11.5px; color: var(--text-muted); flex-wrap: wrap;">
              <span style="background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 4px; font-weight: 600;">⏱️ ${item.duration_formatted}</span>
              <span style="background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 4px;">📦 ${item.size_mb}</span>
              ${statusBadgeHtml}
            </div>
          </div>
        </div>

        <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
          ${actionBtnHtml}
          <button type="button" class="btn-delete-library-audio" data-filename="${item.filename}" data-id="${item.id}" title="${(status === 'waiting' || status === 'uploading') ? 'আপলোড বাতিল করুন' : 'মুছে ফেলুন'}" style="background: #dc2626; border: 1px solid #ef4444; color: #ffffff; border-radius: 8px; padding: 7px 12px; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.4); transition: all 0.2s ease;">
            <span style="display: inline-block; filter: brightness(0) invert(1);">🗑️</span>
          </button>
        </div>
      </div>
    `;
  }).join('');

  // Add click listeners to play buttons
  bodyEl.querySelectorAll('.library-play-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (btn.disabled) return;
      const id = btn.getAttribute('data-id');
      const url = btn.getAttribute('data-url');
      if (url) toggleLibraryAudioPreview(id, url);
    });
  });

  // Add click listeners to select buttons
  bodyEl.querySelectorAll('.btn-select-library-audio').forEach(btn => {
    btn.addEventListener('click', () => {
      const filename = btn.getAttribute('data-filename');
      const duration = parseFloat(btn.getAttribute('data-duration')) || 0;
      const sizeMb = btn.getAttribute('data-sizemb');
      const url = btn.getAttribute('data-url');
      const id = btn.getAttribute('data-id');

      selectAudioFromLibrary({ filename, duration, sizeMb, url, id });
    });
  });

  // Add click listeners to retry buttons
  bodyEl.querySelectorAll('.btn-retry-library-audio').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      const item = audioLibraryData.find(a => a.id === id);
      if (item && item.file) {
        item.upload_status = 'waiting';
        audioUploadQueue.push(item);
        renderAudioLibraryList();
        processAudioUploadQueue();
      }
    });
  });

  // Add click listeners to delete buttons
  bodyEl.querySelectorAll('.btn-delete-library-audio').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const fn = btn.getAttribute('data-filename');
      const id = btn.getAttribute('data-id');

      const isCurrent = currentUploadingItem && (currentUploadingItem.id === id || currentUploadingItem.filename === fn);
      const queueIdx = audioUploadQueue.findIndex(q => q.id === id || q.filename === fn);

      // CASE 1: Currently uploading item is deleted / cancelled
      if (isCurrent || (queueIdx === 0 && isAudioUploading)) {
        if (!confirm(`আপনি কি '${fn}' অডিও আপলোড বাতিল ও মুছে ফেলতে চান?`)) return;

        // Invalidate current upload session so old finally block will not touch state
        currentUploadSessionId++;

        // Immediately abort active HTTP upload stream
        if (currentUploadXhr) {
          try {
            currentUploadXhr.abort();
          } catch (err) {}
          currentUploadXhr = null;
        }
        currentUploadingItem = null;
        isAudioUploading = false;

        // Remove from list and queue
        audioUploadQueue = audioUploadQueue.filter(q => q.id !== id && q.filename !== fn);
        audioLibraryData = audioLibraryData.filter(a => a.id !== id && a.filename !== fn);

        // Tell server to delete any partial or temporary files
        fetch('/api/audio_library/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: fn })
        }).catch(() => {});

        showNotification(`⏹️ '${fn}' আপলোড বাতিল করা হয়েছে। পরবর্তী অডিও আপলোড শুরু হচ্ছে...`);
        renderAudioLibraryList();

        // Immediately start next waiting upload in queue if any
        if (audioUploadQueue.length > 0) {
          setTimeout(() => {
            processAudioUploadQueue();
          }, 50);
        } else {
          const btnUpload = $('btnUploadToAudioLibrary');
          if (btnUpload) {
            btnUpload.disabled = false;
            btnUpload.innerHTML = '⬆️ অডিও আপলোড';
          }
        }
        return;
      }

      // CASE 2: Item is in queue waiting to be uploaded
      if (queueIdx > 0) {
        if (!confirm(`আপনি কি '${fn}' অডিও আপলোড কিউ থেকে মুছে ফেলতে চান?`)) return;
        audioUploadQueue.splice(queueIdx, 1);
        audioLibraryData = audioLibraryData.filter(a => a.id !== id && a.filename !== fn);
        renderAudioLibraryList();
        showNotification(`ℹ️ '${fn}' আপলোড কিউ থেকে মুছে ফেলা হয়েছে।`);
        return;
      }

      // CASE 3: Item had an upload error or is a temporary queue item
      const inData = audioLibraryData.find(a => a.id === id || a.filename === fn);
      if (inData && inData.upload_status === 'error') {
        audioLibraryData = audioLibraryData.filter(a => a.id !== id && a.filename !== fn);
        renderAudioLibraryList();
        fetch('/api/audio_library/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: fn })
        }).catch(() => {});
        return;
      }

      // CASE 4: Standard delete of uploaded file from server library
      if (!confirm(`আপনি কি '${fn}' অডিও ফাইলটি লাইব্রেরি থেকে মুছে ফেলতে চান?`)) return;
      try {
        const res = await fetch('/api/audio_library/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: fn })
        });
        const json = await res.json();
        if (json.success) {
          audioLibraryData = audioLibraryData.filter(a => a.filename !== fn && a.id !== id);
          renderAudioLibraryList();
          showNotification(`🗑️ '${fn}' মুছে ফেলা হয়েছে।`);
          fetchAndRenderAudioLibrary(false);
        } else {
          alert('Delete failed: ' + (json.error || 'অজানা সমস্যা'));
        }
      } catch (err) {
        alert('Delete failed: ' + err.message);
      }
    });
  });
}

function toggleLibraryAudioPreview(id, url) {
  if (currentPlayingAudioId === id && activeLibraryAudioPlayer) {
    if (activeLibraryAudioPlayer.paused) {
      activeLibraryAudioPlayer.play();
      updatePlayBtnIcons(id, true);
    } else {
      activeLibraryAudioPlayer.pause();
      updatePlayBtnIcons(id, false);
    }
    return;
  }

  stopLibraryAudioPreview();

  const fullUrl = url.startsWith('http') ? url : (window.location.origin + url);
  activeLibraryAudioPlayer = new Audio(fullUrl);
  currentPlayingAudioId = id;
  updatePlayBtnIcons(id, true);

  activeLibraryAudioPlayer.play().catch(e => {
    console.warn('Audio preview play error:', e);
    stopLibraryAudioPreview();
  });

  activeLibraryAudioPlayer.onended = () => {
    stopLibraryAudioPreview();
  };
}

function updatePlayBtnIcons(playingId, isPlaying) {
  $$('.library-play-btn').forEach(btn => {
    const id = btn.getAttribute('data-id');
    if (id === playingId && isPlaying) {
      btn.innerHTML = '⏸';
      btn.style.background = '#10b981';
      btn.classList.add('playing');
    } else {
      btn.innerHTML = '▶';
      btn.style.background = 'rgba(255,255,255,0.1)';
      btn.classList.remove('playing');
    }
  });
}

function selectAudioFromLibrary(item) {
  const slot = getActiveSlot();
  if (!slot) return;

  slot.audioName = item.filename;
  slot.audioDuration = item.duration;
  slot.audioUrl = item.url;
  slot.audioLibraryFilename = item.filename;
  slot.audioSizeMb = (item.sizeMb || '0').replace(' MB', '');
  slot.audioFile = null;
  slot.audioDataUrl = null;
  slot.audioAssetId = item.id;

  renderAudioUI(slot);
  updateSegmentEstimates();
  saveStudioState();
  closeAudioLibraryModal();

  appendLog(`[${getTimeString()}] 🎵 Selected '${item.filename}' (${formatTime(item.duration)} · ${item.sizeMb}) from Audio Library for ${slot.name}`, 'success');
}

function openFullscreenModal(videoUrl, filename, url720p = null, filename720p = null, size1080pMb = null, size720pMb = null, displayTitle = null) {
  const modal = $('fullscreenModal');
  const videoEl = $('modalVideoPlayer');
  const titleEl = $('modalVideoTitle');
  const dl1080Btn = $('modalDownloadBtn1080p');
  const dl720Btn = $('modalDownloadBtn720p');
  const mainVid = $('mainVideoPlayer');

  // Pause main player to avoid dual audio
  if (mainVid) mainVid.pause();

  const safeUrl1080 = videoUrl ? encodeURI(decodeURI(videoUrl)) : '';
  const safeUrl720p = url720p ? encodeURI(decodeURI(url720p)) : (safeUrl1080 ? safeUrl1080.replace('.mp4', '_720p.mp4') : '');
  const streamTarget = safeUrl720p || safeUrl1080;
  const posterTarget = (safeUrl1080 ? safeUrl1080.replace('.mp4', '.jpg') : '') || (safeUrl720p ? safeUrl720p.replace('_720p.mp4', '.jpg').replace('.mp4', '.jpg') : '');
  const fn1080 = filename || 'talking_avatar_1080p.mp4';
  const fn720 = filename720p || (filename ? filename.replace('.mp4', '_720p.mp4') : 'talking_avatar_720p.mp4');

  if (modal && videoEl && streamTarget) {
    if (posterTarget) videoEl.poster = posterTarget;
    videoEl.pause();
    videoEl.removeAttribute('src');
    videoEl.src = streamTarget;
    videoEl.innerHTML = `<source src="${streamTarget}" type="video/mp4">`;
    videoEl.currentTime = 0;
    videoEl.muted = false;
    videoEl.load();

    const onModalFrameReady = () => {
      try {
        if (videoEl.paused && videoEl.currentTime === 0) {
          videoEl.currentTime = 0.01;
        }
      } catch (e) {}
    };
    videoEl.addEventListener('loadeddata', onModalFrameReady, { once: true });
    videoEl.addEventListener('loadedmetadata', onModalFrameReady, { once: true });

    const p = videoEl.play();
    if (p !== undefined) {
      p.catch(() => {
        videoEl.muted = true;
        videoEl.play().catch(() => {
          onModalFrameReady();
        });
      });
    }
    if (titleEl) {
      const cardInfo = getVideoCardInfo({ filename: filename });
      titleEl.textContent = displayTitle || cardInfo.fullDisplayTitle || filename || 'Talking Avatar Video Preview';
    }

    if (dl1080Btn) {
      dl1080Btn.innerHTML = `📥 1080P (${size1080pMb ? `${size1080pMb} MB` : 'Full HD'})`;
      const dlUrl1080 = safeUrl1080.includes('?') ? `${safeUrl1080}&download=1` : `${safeUrl1080}?download=1`;
      dl1080Btn.href = dlUrl1080;
      dl1080Btn.download = fn1080;
      dl1080Btn.dataset.url = dlUrl1080;
      dl1080Btn.dataset.filename = fn1080;
      dl1080Btn.onclick = (e) => handleTurboDownloadClick(dl1080Btn, e);
    }

    if (dl720Btn) {
      dl720Btn.innerHTML = `⚡ 720P (${size720pMb ? `${size720pMb} MB` : 'Fast'})`;
      const dlUrl720 = safeUrl720p.includes('?') ? `${safeUrl720p}&download=1` : `${safeUrl720p}?download=1`;
      dl720Btn.href = dlUrl720;
      dl720Btn.download = fn720;
      dl720Btn.dataset.url = dlUrl720;
      dl720Btn.dataset.filename = fn720;
      dl720Btn.onclick = (e) => handleTurboDownloadClick(dl720Btn, e);
    }

    modal.classList.remove('hidden');
  }
}

function handleDeleteSingleVideoClick(btn) {
  const fn = btn.getAttribute('data-filename');
  if (fn) {
    deleteSingleVideo(fn);
  }
}

// ==========================================
// 9. Gallery Management
// ==========================================
function initGalleryControls() {
  const selectAllCheckbox = $('selectAllGallery');
  const btnDeleteSelected = $('btnDeleteSelected');
  const btnDeleteAll = $('btnDeleteAll');

  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', () => {
      const checkboxes = $$('.gallery-card-checkbox');
      checkboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
        const card = cb.closest('.gallery-card');
        if (card) card.classList.toggle('selected', selectAllCheckbox.checked);
      });
      updateBatchDeleteUI();
    });
  }

  if (btnDeleteSelected) {
    btnDeleteSelected.addEventListener('click', async () => {
      const checkedBoxes = $$('.gallery-card-checkbox:checked');
      if (checkedBoxes.length === 0) return;

      const filenames = Array.from(checkedBoxes).map(cb => cb.dataset.filename).filter(Boolean);
      lastRenderedGalleryKey = '';

      // Instant optimistic removal from UI
      checkedBoxes.forEach(cb => {
        const card = cb.closest('.gallery-card');
        if (card) card.remove();
      });

      // Clear output state from any matching slots immediately
      studioState.slots.forEach(slot => {
        if (slot.outputFilename && filenames.some(fn => fn === slot.outputFilename || fn === slot.outputFilename720p || slot.outputFilename.includes(fn))) {
          slot.status = 'idle';
          slot.outputVideoUrl = null;
          slot.outputFilename = null;
          slot.fileSizeMb = null;
          slot.outputVideoUrl720p = null;
          slot.outputFilename720p = null;
          slot.taskId = null;
          if (slot.id === studioState.activeSlotId) {
            resetVideoPlayerUI(slot.name);
          }
        }
      });
      saveStudioState();
      renderSlotTabs();
      updateButtonStates();

      try {
        const res = await fetch('/api/gallery/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filenames })
        });
        if (res.ok) {
          await fetchGallery();
        }
      } catch (e) {
        console.error('Failed to delete selected videos:', e);
      }
    });
  }

  if (btnDeleteAll) {
    btnDeleteAll.addEventListener('click', async () => {
      lastRenderedGalleryKey = '';
      const grid = $('galleryGrid');
      if (grid) grid.innerHTML = '';

      // Clear all completed slot outputs
      studioState.slots.forEach(slot => {
        if (slot.status === 'completed' || slot.outputVideoUrl) {
          slot.status = 'idle';
          slot.outputVideoUrl = null;
          slot.outputFilename = null;
          slot.fileSizeMb = null;
          slot.outputVideoUrl720p = null;
          slot.outputFilename720p = null;
          slot.taskId = null;
          if (slot.id === studioState.activeSlotId) {
            resetVideoPlayerUI(slot.name);
          }
        }
      });
      saveStudioState();
      renderSlotTabs();
      updateButtonStates();

      try {
        const res = await fetch('/api/gallery/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ all: true })
        });
        if (res.ok) {
          await fetchGallery();
        }
      } catch (e) {
        console.error('Failed to clear gallery:', e);
      }
    });
  }
}

let currentGalleryTab = 'gallery';
let activeGalleryVideos = [];
let trashGalleryVideos = [];
let lastRenderedGalleryKey = '';
let lastRenderedTrashKey = '';

function switchGalleryTab(tab) {
  currentGalleryTab = tab;
  const tabGalleryBtn = $('tabGalleryView');
  const tabTrashBtn = $('tabTrashView');
  const galleryGrid = $('galleryGrid');
  const trashGrid = $('trashGrid');
  const activeBatchActions = $('activeBatchActions');
  const trashBatchActions = $('trashBatchActions');
  const mainHeading = $('galleryMainHeading');

  if (tab === 'trash') {
    if (tabGalleryBtn) tabGalleryBtn.classList.remove('active');
    if (tabTrashBtn) tabTrashBtn.classList.add('active');
    if (galleryGrid) galleryGrid.classList.add('hidden');
    if (trashGrid) trashGrid.classList.remove('hidden');
    if (activeBatchActions) activeBatchActions.classList.add('hidden');
    if (trashBatchActions) trashBatchActions.classList.remove('hidden');
    if (mainHeading) mainHeading.textContent = 'Trash';
    renderTrashCards(trashGalleryVideos);
  } else {
    if (tabGalleryBtn) tabGalleryBtn.classList.add('active');
    if (tabTrashBtn) tabTrashBtn.classList.remove('active');
    if (galleryGrid) galleryGrid.classList.remove('hidden');
    if (trashGrid) trashGrid.classList.add('hidden');
    if (activeBatchActions) activeBatchActions.classList.remove('hidden');
    if (trashBatchActions) trashBatchActions.classList.add('hidden');
    if (mainHeading) mainHeading.textContent = 'Recent Videos';
    renderGalleryCards(activeGalleryVideos);
  }
  updateTrashBatchActionsUI();
  updateBatchDeleteUI();
}

async function fetchGallery() {
  try {
    const res = await fetch('/api/gallery');
    if (!res.ok) return;
    const data = await res.json();
    activeGalleryVideos = data.videos || [];

    const trashRes = await fetch('/api/trash');
    if (trashRes.ok) {
      const trashData = await trashRes.json();
      trashGalleryVideos = trashData.videos || [];
    }

    const activeTabCount = $('tabActiveCount');
    const trashTabCount = $('tabTrashCount');
    if (activeTabCount) activeTabCount.textContent = activeGalleryVideos.length;
    if (trashTabCount) trashTabCount.textContent = trashGalleryVideos.length;

    if (currentGalleryTab === 'trash') {
      renderTrashCards(trashGalleryVideos);
    } else {
      renderGalleryCards(activeGalleryVideos);
    }

    // Sync slots with their matched gallery videos
    studioState.slots.forEach(slot => {
      if (slot.status === 'running' || slot.status === 'queued') return;
      let matched = null;
      if (slot.outputFilename) {
        matched = activeGalleryVideos.find(v => v.filename === slot.outputFilename || v.filename_1080p === slot.outputFilename);
      }
      if (!matched && slot.taskId) {
        matched = activeGalleryVideos.find(v => (v.filename && v.filename.includes(slot.taskId)) || (v.id && v.id.includes(slot.taskId)));
      }
      if (!matched && slot.id === 1 && !slot.outputFilename && activeGalleryVideos.length > 0) {
        matched = activeGalleryVideos.find(v => v.filename && v.filename.startsWith('Video_1'));
      }

      if (matched) {
        slot.status = 'completed';
        slot.outputVideoUrl = matched.url_1080p || matched.url;
        slot.outputFilename = matched.filename_1080p || matched.filename;
        slot.fileSizeMb = matched.size_1080p_mb || matched.size_mb;
        slot.durationFormatted = matched.duration_label;
        slot.generationTimeFormatted = matched.render_time_label;
        slot.outputVideoUrl720p = matched.url_720p;
        slot.outputFilename720p = matched.filename_720p;
        slot.fileSize720pMb = matched.size_720p_mb;
      } else if (slot.outputFilename) {
        // File was deleted from server or moved to trash: cleanly clear slot output
        slot.status = 'idle';
        slot.outputVideoUrl = null;
        slot.outputFilename = null;
        slot.fileSizeMb = null;
        slot.outputVideoUrl720p = null;
        slot.outputFilename720p = null;
        if (slot.id === studioState.activeSlotId) {
          resetVideoPlayerUI(slot.name);
        }
      }
    });

    const activeSlot = getActiveSlot();
    const activeSlotMatched = activeSlot && activeSlot.outputFilename 
      ? activeGalleryVideos.find(v => v.filename === activeSlot.outputFilename || v.filename_1080p === activeSlot.outputFilename) 
      : null;

    if (activeSlot && activeSlot.outputVideoUrl && activeSlotMatched) {
      const targetSrc = activeSlot.outputVideoUrl720p || activeSlotMatched.url_720p || activeSlot.outputVideoUrl;
      const videoPlayer = $('mainVideoPlayer');
      if (!videoPlayer || videoPlayer.dataset.loadedSrc !== targetSrc) {
        loadRenderedVideo(
          activeSlot.outputVideoUrl,
          activeSlot.outputFilename,
          activeSlot.fileSizeMb,
          false,
          activeSlot.name,
          activeSlot.durationFormatted,
          activeSlot.generationTimeFormatted,
          activeSlot.outputVideoUrl720p || activeSlotMatched.url_720p,
          activeSlot.outputFilename720p || activeSlotMatched.filename_720p,
          activeSlot.fileSize720pMb || activeSlotMatched.size_720p_mb
        );
      }
    } else if (activeSlot && !activeSlot.outputVideoUrl) {
      resetVideoPlayerUI(activeSlot.name);
    }

    if (activeSlot) {
      renderProgressUI(activeSlot);
      renderSlotTabs();
    }
  } catch (e) {
    console.warn('Failed to load gallery:', e);
  }
}

function renderGalleryCards(videos) {
  const grid = $('galleryGrid');
  if (!grid) return;

  // Prevent wiping DOM and interrupting live playing videos if gallery has not changed
  const galleryKey = videos.map(v => `${v.id}_${v.filename}_${v.size_mb}_${v.duration_label}_${v.render_time_label}`).join('|');
  if (galleryKey === lastRenderedGalleryKey && grid.children.length === videos.length) {
    return;
  }
  lastRenderedGalleryKey = galleryKey;

  if (videos.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 36px 20px; font-size: 13px; background: #ffffff; border: 1px dashed var(--border-strong); border-radius: var(--radius-md);">
      <div style="font-size: 28px; margin-bottom: 8px;">🎬</div>
      <strong>No videos rendered yet</strong>
      <p style="margin-top: 4px; color: var(--text-muted);">Upload a portrait image and speech audio above to generate your first AI talking avatar!</p>
    </div>`;
    updateBatchDeleteUI();
    return;
  }

  grid.innerHTML = videos.map(v => {
    const rawUrl1080 = v.url_1080p || v.url || `/outputs/${v.filename}`;
    const safeUrl1080 = encodeURI(decodeURI(rawUrl1080));
    const rawUrl720p = v.url_720p || (rawUrl1080 ? rawUrl1080.replace('.mp4', '_720p.mp4') : '');
    const safeUrl720p = encodeURI(decodeURI(rawUrl720p));
    const safeId = (v.id || v.filename).replace(/[^a-zA-Z0-9_-]/g, '_');
    const safeEscapedFilename = escapeHtml(v.filename);
    const fn720 = v.filename_720p || v.filename.replace('.mp4', '_720p.mp4');
    const safeEscapedFn720 = escapeHtml(fn720);
    const s1080 = v.size_1080p_mb || v.size_mb || 0;
    const s720 = v.size_720p_mb || Math.round(s1080 * 0.35);
    const posterUrl = v.poster_url || (safeUrl1080 ? safeUrl1080.replace('.mp4', '.jpg') : '');
    const previewStreamUrl = safeUrl720p || safeUrl1080;
    const dlUrl1080 = safeUrl1080 ? (safeUrl1080.includes('?') ? `${safeUrl1080}&download=1` : `${safeUrl1080}?download=1`) : '';
    const dlUrl720 = safeUrl720p ? (safeUrl720p.includes('?') ? `${safeUrl720p}&download=1` : `${safeUrl720p}?download=1`) : '';
    const cardInfo = getVideoCardInfo(v);

    return `
    <div class="gallery-card" id="card_${safeId}" data-filename="${safeEscapedFilename}" data-url="${safeUrl1080}" data-url-720p="${safeUrl720p}" data-filename-720p="${safeEscapedFn720}" data-size-1080p="${s1080}" data-size-720p="${s720}" data-display-title="${escapeHtml(cardInfo.fullDisplayTitle)}">
      <!-- Top Left Checkbox -->
      <div class="gallery-card-checkbox-wrap" onclick="event.stopPropagation();">
        <input type="checkbox" class="gallery-card-checkbox" data-filename="${safeEscapedFilename}" onchange="onCardCheckboxChange(this)">
      </div>

      <!-- Top Right Floating Action Icons (Delete Button Only) -->
      <div class="gallery-quick-actions" onclick="event.stopPropagation();">
        <button type="button" class="btn-card-action btn-delete-card" title="Move to Trash" data-filename="${safeEscapedFilename}" onclick="handleDeleteSingleVideoClick(this)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
          </svg>
        </button>
      </div>

      <!-- Thumbnail (Continuous Full-Length Hover Preview with Default Sound) -->
      <div class="gallery-thumb-wrapper" data-url="${safeUrl1080}" data-url-720p="${safeUrl720p}" data-filename="${safeEscapedFilename}" onmouseenter="onGalleryThumbEnter(this)" onmouseleave="onGalleryThumbLeave(this)" onclick="handleGalleryCardClick(this.closest('.gallery-card'))">
        <video class="gallery-thumb" poster="${posterUrl}" preload="auto" loop playsinline onloadedmetadata="onGalleryVideoLoadedMetadata(this, 'card_${safeId}')">
          <source src="${previewStreamUrl}" type="video/mp4">
        </video>
        <div class="gallery-hover-indicator">
          <span class="indicator-text">🔊 Live Preview</span>
        </div>
      </div>

      <!-- Card Info -->
      <div class="gallery-info" data-url="${safeUrl1080}" data-filename="${safeEscapedFilename}">
        <div class="gallery-title" title="${escapeHtml(cardInfo.fullDisplayTitle)}" onclick="handleGalleryCardClick(this.closest('.gallery-card'))"><span class="gallery-title-slot">${escapeHtml(cardInfo.slotLabel)}:</span> ${escapeHtml(cardInfo.title)}</div>
        <div class="gallery-meta">
          <span class="gallery-meta-tag gallery-duration-tag" title="Exact Video Duration">⏱️ ${v.duration_label || 'Full Video'}</span>
          <span class="gallery-meta-tag gallery-resolution-tag" title="Neural DiT Generation Resolution">🎯 <strong>${escapeHtml(v.resolution_label || (v.resolution ? v.resolution.toUpperCase() + ' DiT' : '500p DiT'))}</strong></span>
          <span class="gallery-meta-tag gallery-tag-720p" title="Total Render Generation Time">⚡ <strong>${formatRenderTimeDisplay(v.render_time_label)}</strong></span>
        </div>

        <!-- Full-Width Dual Green Download Buttons Stack -->
        <div class="gallery-card-download-stack" onclick="event.stopPropagation();">
          <a href="${dlUrl720}" download="${safeEscapedFn720}" data-url="${dlUrl720}" data-filename="${safeEscapedFn720}" class="btn-card-dl-btn btn-dl-720p" title="Download 720P Fast Preview (${s720} MB)" onclick="handleTurboDownloadClick(this, event);">
            <div class="dl-btn-content">
              <span class="dl-icon">⚡</span>
              <span class="dl-text">Download 720P HD</span>
            </div>
            <span class="dl-size-badge">${s720} MB</span>
          </a>

          <a href="${dlUrl1080}" download="${safeEscapedFilename}" data-url="${dlUrl1080}" data-filename="${safeEscapedFilename}" class="btn-card-dl-btn btn-dl-1080p" title="Download 1080P Ultra-HD Master (${s1080} MB)" onclick="handleTurboDownloadClick(this, event);">
            <div class="dl-btn-content">
              <span class="dl-icon">🎬</span>
              <span class="dl-text">Download 1080P Full HD</span>
            </div>
            <span class="dl-size-badge">${s1080} MB</span>
          </a>
        </div>
      </div>
    </div>
    `;
  }).join('');

  updateBatchDeleteUI();
}

function renderTrashCards(videos) {
  const grid = $('trashGrid');
  if (!grid) return;

  const trashKey = videos.map(v => `${v.id}_${v.filename}_${v.size_mb}`).join('|');
  if (trashKey === lastRenderedTrashKey && grid.children.length === videos.length) {
    return;
  }
  lastRenderedTrashKey = trashKey;

  if (videos.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 36px 20px; font-size: 13px; background: #ffffff; border: 1px dashed var(--border-strong); border-radius: var(--radius-md);">
      <div style="font-size: 28px; margin-bottom: 8px;">🗑️</div>
      <strong>Trash is Empty</strong>
      <p style="margin-top: 4px; color: var(--text-muted);">Deleted videos will appear here. You can recover them anytime or permanently delete them.</p>
    </div>`;
    updateTrashBatchActionsUI();
    return;
  }

  grid.innerHTML = videos.map(v => {
    const rawUrl1080 = v.url_1080p || v.url || `/outputs/.trash/${v.filename}`;
    const safeUrl1080 = encodeURI(decodeURI(rawUrl1080));
    const rawUrl720p = v.url_720p || (rawUrl1080 ? rawUrl1080.replace('.mp4', '_720p.mp4') : '');
    const safeUrl720p = encodeURI(decodeURI(rawUrl720p));
    const safeId = (v.id || v.filename).replace(/[^a-zA-Z0-9_-]/g, '_');
    const safeEscapedFilename = escapeHtml(v.filename);
    const s1080 = v.size_1080p_mb || v.size_mb || 0;
    const posterUrl = v.poster_url || (safeUrl1080 ? safeUrl1080.replace('.mp4', '.jpg') : '');
    const previewStreamUrl = safeUrl720p || safeUrl1080;
    const cardInfo = getVideoCardInfo(v);

    return `
    <div class="gallery-card trash-card" id="trash_card_${safeId}" data-filename="${safeEscapedFilename}" data-url="${safeUrl1080}" data-url-720p="${safeUrl720p}" data-display-title="${escapeHtml(cardInfo.fullDisplayTitle)}">
      <!-- Top Left Checkbox -->
      <div class="gallery-card-checkbox-wrap" onclick="event.stopPropagation();">
        <input type="checkbox" class="trash-card-checkbox" data-filename="${safeEscapedFilename}" onchange="onTrashCardCheckboxChange(this)">
      </div>

      <!-- Thumbnail -->
      <div class="gallery-thumb-wrapper" data-url="${safeUrl1080}" data-url-720p="${safeUrl720p}" data-filename="${safeEscapedFilename}" onmouseenter="onGalleryThumbEnter(this)" onmouseleave="onGalleryThumbLeave(this)" onclick="handleGalleryCardClick(this.closest('.gallery-card'))">
        <video class="gallery-thumb" poster="${posterUrl}" preload="auto" loop playsinline>
          <source src="${previewStreamUrl}" type="video/mp4">
        </video>
        <div class="gallery-hover-indicator">
          <span class="indicator-text">🔊 Live Preview</span>
        </div>
      </div>

      <!-- Card Info -->
      <div class="gallery-info">
        <div class="gallery-title" title="${escapeHtml(cardInfo.fullDisplayTitle)}" onclick="handleGalleryCardClick(this.closest('.gallery-card'))"><span class="gallery-title-slot">${escapeHtml(cardInfo.slotLabel)}:</span> ${escapeHtml(cardInfo.title)}</div>
        <div class="gallery-meta">
          <span class="gallery-meta-tag gallery-duration-tag" title="Video Duration">⏱️ ${v.duration_label || 'Full Video'}</span>
          <span class="gallery-meta-tag" style="background: #fee2e2; color: #dc2626;" title="In Trash">🗑️ <strong>${s1080} MB</strong></span>
        </div>

        <!-- Action Buttons: Recover & Permanent Delete -->
        <div class="gallery-card-download-stack" style="gap: 5px; margin-top: 6px; padding-top: 6px;" onclick="event.stopPropagation();">
          <button type="button" class="btn-card-trash-recover" title="Recover video back to Recent Videos" onclick="handleRecoverSingleVideo('${safeEscapedFilename}')">
            <span>♻️ Recover Video</span>
          </button>
          <button type="button" class="btn-card-trash-delete" title="Permanently delete video from server" onclick="handlePermanentDeleteSingleVideo('${safeEscapedFilename}')">
            <span>🔥 Delete Permanently</span>
          </button>
        </div>
      </div>
    </div>
    `;
  }).join('');

  updateTrashBatchActionsUI();
}

async function handleRecoverSingleVideo(filename) {
  try {
    const res = await fetch('/api/trash/recover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames: [filename] })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[${getTimeString()}] ♻️ Recovered video: ${filename}`, 'success');
      lastRenderedGalleryKey = '';
      lastRenderedTrashKey = '';
      await fetchGallery();
    }
  } catch (e) {
    console.error('Failed to recover video:', e);
  }
}

async function handlePermanentDeleteSingleVideo(filename) {
  if (!confirm(`Permanently delete "${filename}"? This action CANNOT be undone and will erase all video data completely from the server.`)) {
    return;
  }
  try {
    const res = await fetch('/api/trash/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames: [filename] })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[${getTimeString()}] 🔥 Permanently deleted: ${filename}`, 'warning');
      lastRenderedTrashKey = '';
      await fetchGallery();
    }
  } catch (e) {
    console.error('Failed to permanently delete video:', e);
  }
}

async function handleRecoverSelectedTrash() {
  const checked = $$('.trash-card-checkbox:checked');
  if (checked.length === 0) return;
  const filenames = Array.from(checked).map(c => c.getAttribute('data-filename')).filter(Boolean);
  try {
    const res = await fetch('/api/trash/recover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[${getTimeString()}] ♻️ Recovered ${filenames.length} video(s) to Recent Videos`, 'success');
      lastRenderedGalleryKey = '';
      lastRenderedTrashKey = '';
      await fetchGallery();
    }
  } catch (e) {
    console.error('Failed to recover selected videos:', e);
  }
}

async function handleDeleteSelectedTrashPermanent() {
  const checked = $$('.trash-card-checkbox:checked');
  if (checked.length === 0) return;
  const filenames = Array.from(checked).map(c => c.getAttribute('data-filename')).filter(Boolean);
  if (!confirm(`Permanently delete ${filenames.length} selected video(s)? This CANNOT be undone.`)) {
    return;
  }
  try {
    const res = await fetch('/api/trash/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[${getTimeString()}] 🔥 Permanently deleted ${filenames.length} video(s)`, 'warning');
      lastRenderedTrashKey = '';
      await fetchGallery();
    }
  } catch (e) {
    console.error('Failed to permanently delete selected videos:', e);
  }
}

async function handleEmptyTrash() {
  if (trashGalleryVideos.length === 0) return;
  if (!confirm(`Empty entire Trash (${trashGalleryVideos.length} video(s))? This will PERMANENTLY erase all trashed videos from the server.`)) {
    return;
  }
  try {
    const res = await fetch('/api/trash/empty', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ all: true })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[${getTimeString()}] 🗑️ Emptied entire Trash`, 'warning');
      lastRenderedTrashKey = '';
      await fetchGallery();
    }
  } catch (e) {
    console.error('Failed to empty trash:', e);
  }
}

function onTrashCardCheckboxChange(checkbox) {
  const card = checkbox.closest('.trash-card');
  if (card) card.classList.toggle('selected', checkbox.checked);
  updateTrashBatchActionsUI();
}

function onSelectAllTrashChange(selectAllCheckbox) {
  const checkboxes = $$('.trash-card-checkbox');
  checkboxes.forEach(c => {
    c.checked = selectAllCheckbox.checked;
    const card = c.closest('.trash-card');
    if (card) card.classList.toggle('selected', selectAllCheckbox.checked);
  });
  updateTrashBatchActionsUI();
}

function updateTrashBatchActionsUI() {
  const checkboxes = $$('.trash-card-checkbox');
  const checked = $$('.trash-card-checkbox:checked');
  const selectAll = $('selectAllTrashCheckbox');
  const btnRecover = $('btnRecoverSelectedTrash');
  const btnDelete = $('btnDeleteSelectedTrash');
  const btnEmpty = $('btnEmptyTrash');

  if (selectAll && checkboxes.length > 0) {
    selectAll.checked = (checked.length === checkboxes.length);
    selectAll.indeterminate = (checked.length > 0 && checked.length < checkboxes.length);
  }

  if (btnRecover) btnRecover.disabled = (checked.length === 0);
  if (btnDelete) btnDelete.disabled = (checked.length === 0);
  if (btnEmpty) btnEmpty.disabled = (trashGalleryVideos.length === 0);
}

window.onGalleryVideoLoadedMetadata = function(videoEl, cardId) {
  if (!videoEl || !videoEl.duration || isNaN(videoEl.duration)) return;
  try {
    if (videoEl.paused && videoEl.currentTime === 0) {
      videoEl.currentTime = 0.01;
    }
  } catch (e) {}
  const durSec = Math.round(videoEl.duration * 10) / 10;
  let formatted = '';
  if (durSec >= 60) {
    const m = Math.floor(durSec / 60);
    const s = Math.floor(durSec % 60);
    formatted = `${m}m ${s}s`;
  } else {
    formatted = `${durSec}s`;
  }
  const card = document.getElementById(cardId);
  if (card) {
    const durTag = card.querySelector('.gallery-duration-tag');
    if (durTag) {
      durTag.innerHTML = `⏱️ ${formatted}`;
    }
  }
};

function handleDownloadCardClick(btn, e) {
  if (e) e.stopPropagation();
  const filename = btn.getAttribute('data-filename');
  const url = btn.getAttribute('data-url');
  if (url) downloadVideoFile(filename || 'video.mp4', url);
}

function handleGalleryCardClick(el) {
  if (!el) return;
  const url = el.getAttribute('data-url');
  const fn = el.getAttribute('data-filename');
  const url720 = el.getAttribute('data-url-720p');
  const fn720 = el.getAttribute('data-filename-720p');
  const s1080 = el.getAttribute('data-size-1080p');
  const s720 = el.getAttribute('data-size-720p');
  const displayTitle = el.getAttribute('data-display-title') || el.querySelector('.gallery-title')?.getAttribute('title') || fn;
  if (url) {
    openFullscreenModal(url, fn, url720, fn720, s1080, s720, displayTitle);
  }
}

function onGalleryThumbEnter(thumbWrapper) {
  const vid = thumbWrapper.querySelector('video.gallery-thumb');
  const indicator = thumbWrapper.querySelector('.gallery-hover-indicator .indicator-text');
  if (!vid) return;

  // Unmuted by default per user directive
  vid.muted = false;
  vid.volume = 1.0;

  const p = vid.play();
  if (p !== undefined) {
    p.then(() => {
      if (indicator) indicator.textContent = '🔊 Live Audio Playing';
    }).catch(err => {
      // Browser autoplay restriction fallback: play muted until document clicked
      vid.muted = true;
      vid.play().then(() => {
        if (indicator) indicator.textContent = '▶️ Playing (Click video for audio)';
      }).catch(() => {});
    });
  }
}

function onGalleryThumbLeave(thumbWrapper) {
  const vid = thumbWrapper.querySelector('video.gallery-thumb');
  if (vid) {
    vid.pause();
  }
}

function onCardCheckboxChange(checkbox) {
  const card = checkbox.closest('.gallery-card');
  if (card) card.classList.toggle('selected', checkbox.checked);
  updateBatchDeleteUI();
}

function updateBatchDeleteUI() {
  const checkboxes = $$('.gallery-card-checkbox');
  const checked = $$('.gallery-card-checkbox:checked');
  const selectAll = $('selectAllGallery');
  const btnDeleteSelected = $('btnDeleteSelected');
  const btnDeleteAll = $('btnDeleteAll');
  const deleteCountText = $('deleteSelectedCount');

  if (selectAll && checkboxes.length > 0) {
    selectAll.checked = (checked.length === checkboxes.length);
    selectAll.indeterminate = (checked.length > 0 && checked.length < checkboxes.length);
  }

  if (btnDeleteSelected) {
    btnDeleteSelected.disabled = (checked.length === 0);
    if (deleteCountText) deleteCountText.textContent = checked.length > 0 ? ` (${checked.length})` : '';
  }

  if (btnDeleteAll) {
    btnDeleteAll.disabled = (checkboxes.length === 0);
  }
}

async function deleteSingleVideo(filename) {
  // Instant deletion with zero confirmation popup per user directive
  const safeId = filename.replace(/[^a-zA-Z0-9_-]/g, '_');
  const cardEl = document.getElementById(`card_${safeId}`) || document.querySelector(`[data-filename="${filename}"]`);
  if (cardEl) {
    cardEl.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
    cardEl.style.opacity = '0';
    cardEl.style.transform = 'scale(0.95)';
    setTimeout(() => { if (cardEl) cardEl.remove(); }, 150);
  }

  lastRenderedGalleryKey = ''; // Invalidate gallery cache

  // Instantly clear from matching slot in UI and storage
  studioState.slots.forEach(slot => {
    if (slot.outputFilename === filename || slot.outputFilename720p === filename || (slot.outputFilename && slot.outputFilename.includes(filename))) {
      slot.status = 'idle';
      slot.outputVideoUrl = null;
      slot.outputFilename = null;
      slot.fileSizeMb = null;
      slot.outputVideoUrl720p = null;
      slot.outputFilename720p = null;
      slot.taskId = null;
      if (slot.id === studioState.activeSlotId) {
        resetVideoPlayerUI(slot.name);
      }
    }
  });
  saveStudioState();
  renderSlotTabs();
  updateButtonStates();

  try {
    const res = await fetch('/api/gallery/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames: [filename] })
    });
    await res.json();
    appendLog(`[${getTimeString()}] 🗑️ Deleted video: ${filename}`, 'info');
    await fetchGallery();
  } catch (e) {
    console.error('Failed to delete video:', e);
  }
}

// ==========================================
// 10. Terminal Logging Utilities
// ==========================================
function appendLog(text, type = 'info', targetSlot = null) {
  const slot = targetSlot || getActiveSlot();
  if (slot) {
    slot.logs = slot.logs || [];
    slot.logs.push(text);
  }

  const active = getActiveSlot();
  if (!targetSlot || (active && active.id === targetSlot.id)) {
    const logBody = $('terminalLogBody');
    if (!logBody) return;

    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    div.innerHTML = escapeHtml(text);
    logBody.appendChild(div);
    logBody.scrollTop = logBody.scrollHeight;
  }
}

function renderTerminalLogs(logs) {
  const logBody = $('terminalLogBody');
  if (!logBody) return;

  if (!logs || logs.length === 0) {
    logBody.innerHTML = `<div class="log-line system"><span class="log-ts">[${getTimeString()}]</span> LongCat-Video-Avatar 1.5 Studio ready.</div>`;
    return;
  }

  const cleanedLogs = [];
  logs.forEach(l => {
    if (!l) return;
    // Strip terminal ANSI escape codes and carriage returns
    let text = String(l).replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '').trim();
    if (!text) return;
    cleanedLogs.push(text);
  });

  const lastLogs = cleanedLogs.slice(-100);

  logBody.innerHTML = lastLogs.map(l => {
    let cls = 'info';
    if (l.includes('[SUCCESS]') || l.includes('completed') || l.includes('Finished!') || l.includes('🎯') || l.includes('resolved final output')) cls = 'success';
    else if (l.includes('[ERROR]') || l.includes('[EXCEPTION]') || l.includes('Error')) cls = 'error';
    else if (l.includes('[COLLAPSE DETECTED]') || l.includes('auto-recovering') || l.includes('RE-ANCHOR') || l.includes('⚠️')) cls = 'warning';
    else if (l.includes('[QUALITY]')) cls = 'highlight';
    else if (l.includes('Denoising:')) cls = 'system';
    else if (l.includes('Generating segment')) cls = 'system';
    else if (l.includes('frame=') || l.includes('Saving video') || l.includes('Packaging')) cls = 'info';
    return `<div class="log-line ${cls}">${escapeHtml(l)}</div>`;
  }).join('');

  logBody.scrollTop = logBody.scrollHeight;
}

// ==========================================
// 11. State Persistence (IndexedDB + LocalStorage)
// ==========================================
const DB_NAME = 'LongCatStudioDB_v2';
const DB_STORE = 'slots_store';

function openStudioDB() {
  return new Promise((resolve) => {
    if (!window.indexedDB) {
      resolve(null);
      return;
    }
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(DB_STORE)) {
        db.createObjectStore(DB_STORE, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => {
      console.warn('IndexedDB open error:', request.error);
      resolve(null);
    };
  });
}

async function saveStudioState() {
  saveActiveSlotFromDOM();
  
  const serializedSlots = studioState.slots.map(s => ({
    id: s.id,
    name: s.name,
    title: s.title || '',
    imageName: s.imageName,
    imageDataUrl: s.imageDataUrl,
    imageDimensions: s.imageDimensions,
    imageSizeMb: s.imageSizeMb,
    imageAssetId: s.imageAssetId,
    imageUrl: s.imageUrl,

    audioName: s.audioName,
    audioDataUrl: s.audioDataUrl,
    audioDuration: s.audioDuration,
    audioSizeMb: s.audioSizeMb,
    audioAssetId: s.audioAssetId,
    audioUrl: s.audioUrl,
    audioLibraryFilename: s.audioLibraryFilename,

    selectedRatio: s.selectedRatio || 'auto',
    selectedResolution: (s.selectedResolution && s.selectedResolution !== 'auto') ? s.selectedResolution : '500p',
    generationMode: s.generationMode || 'anchor_seamless',
    numFrames: s.numFrames || 205,
    gender: s.gender || '',
    detectedGender: s.detectedGender || '',
    detectedRatio: s.detectedRatio || '9:16',
    detectedResolution: s.detectedResolution || '1080x1920',
    detectedQualityLabel: s.detectedQualityLabel || 'Full HD Portrait',
    detectedRatioTitle: s.detectedRatioTitle || '9:16 Portrait (Reels / Shorts)',

    selectedPreset: s.selectedPreset,
    selectedSteps: s.selectedSteps,
    stepBooster: s.stepBooster,
    lengthMode: s.lengthMode,
    prompt: s.prompt,
    negativePrompt: s.negativePrompt,
    seed: s.seed,

    taskId: s.taskId,
    status: s.status,
    progress: s.progress,
    stage: s.stage,
    outputVideoUrl: s.outputVideoUrl,
    outputFilename: s.outputFilename,
    fileSizeMb: s.fileSizeMb,
    outputVideoUrl720p: s.outputVideoUrl720p,
    outputFilename720p: s.outputFilename720p,
    fileSize720pMb: s.fileSize720pMb,
    durationFormatted: s.durationFormatted,
    generationTimeFormatted: s.generationTimeFormatted
  }));

  // 1. Immediately save lightweight metadata to localStorage (Instant synchronous save)
  try {
    localStorage.setItem('longcat_active_slot_id', studioState.activeSlotId.toString());
    const lightSlots = serializedSlots.map(s => ({
      id: s.id,
      name: s.name,
      title: s.title || '',
      imageName: s.imageName,
      imageDimensions: s.imageDimensions,
      imageSizeMb: s.imageSizeMb,
      imageAssetId: s.imageAssetId,
      imageUrl: s.imageUrl,
      audioName: s.audioName,
      audioDuration: s.audioDuration,
      audioSizeMb: s.audioSizeMb,
      audioAssetId: s.audioAssetId,
      audioUrl: s.audioUrl,
      audioLibraryFilename: s.audioLibraryFilename,
      num_segments: s.num_segments || (s.taskData && s.taskData.num_segments) || (s.audioDuration ? Math.ceil(s.audioDuration / 8) : 1),
      total_segments: s.total_segments || (s.taskData && s.taskData.total_segments) || (s.audioDuration ? Math.ceil(s.audioDuration / 8) : 1),
      taskData: s.taskData,
      logs: (s.logs && s.logs.length > 0) ? s.logs.slice(-50) : [],
      selectedRatio: s.selectedRatio || 'auto',
      selectedResolution: (s.selectedResolution && s.selectedResolution !== 'auto') ? s.selectedResolution : '500p',
      generationMode: s.generationMode || 'anchor_seamless',
      numFrames: s.numFrames || 205,
      gender: s.gender || '',
      detectedGender: s.detectedGender || '',
      detectedRatio: s.detectedRatio || '9:16',
      detectedResolution: s.detectedResolution || '1080x1920',
      detectedQualityLabel: s.detectedQualityLabel || 'Full HD Portrait',
      detectedRatioTitle: s.detectedRatioTitle || '9:16 Portrait (Reels / Shorts)',
      selectedPreset: s.selectedPreset,
      selectedSteps: s.selectedSteps,
      stepBooster: s.stepBooster,
      lengthMode: s.lengthMode,
      prompt: s.prompt,
      negativePrompt: s.negativePrompt,
      seed: s.seed,
      taskId: s.taskId,
      status: s.status,
      progress: s.progress,
      stage: s.stage,
      outputVideoUrl: s.outputVideoUrl,
      outputFilename: s.outputFilename,
      fileSizeMb: s.fileSizeMb,
      outputVideoUrl720p: s.outputVideoUrl720p,
      outputFilename720p: s.outputFilename720p,
      fileSize720pMb: s.fileSize720pMb,
      durationFormatted: s.durationFormatted,
      generationTimeFormatted: s.generationTimeFormatted
    }));
    localStorage.setItem('longcat_studio_slots_meta', JSON.stringify(lightSlots));

    // Cross-device sync: debounce POST to server
    debouncedSyncServerState(lightSlots, studioState.activeSlotId);

    // Save individual slot gender keys
    for (const s of serializedSlots) {
      if (s.gender) {
        localStorage.setItem(`longcat_slot_${s.id}_gender`, s.gender);
      }
    }
  } catch (e) {}

  // 2. Save full binary data to IndexedDB (asynchronous & non-destructive)
  try {
    const db = await openStudioDB();
    if (db) {
      const tx = db.transaction(DB_STORE, 'readwrite');
      const store = tx.objectStore(DB_STORE);
      for (const slot of serializedSlots) {
        const getReq = store.get(slot.id);
        getReq.onsuccess = () => {
          const existing = getReq.result;
          if (existing) {
            if (!slot.imageDataUrl && existing.imageDataUrl) {
              slot.imageDataUrl = existing.imageDataUrl;
            }
            if (!slot.audioDataUrl && existing.audioDataUrl) {
              slot.audioDataUrl = existing.audioDataUrl;
            }
          }
          store.put(slot);
        };
        getReq.onerror = () => {
          store.put(slot);
        };
      }
    }
  } catch (e) {
    console.warn('IndexedDB save error:', e);
  }
}

function restoreStateFastSync() {
  try {
    const savedSlotsJson = localStorage.getItem('longcat_studio_slots_meta') || localStorage.getItem('longcat_studio_slots');
    let loadedSlots = [];
    if (savedSlotsJson) {
      const parsed = JSON.parse(savedSlotsJson);
      if (Array.isArray(parsed) && parsed.length > 0) {
        loadedSlots = parsed;
      }
    }

    if (Array.isArray(loadedSlots) && loadedSlots.length > 0) {
      const seenIds = new Set();
      const seenNames = new Set();
      const cleanSlots = [];
      for (const s of loadedSlots) {
        if (!s || seenIds.has(s.id) || seenNames.has(s.name)) continue;
        seenIds.add(s.id);
        seenNames.add(s.name);
        const fresh = createSlot(s.id, s.name);
        const merged = Object.assign(fresh, s);
        if (!merged.imageUrl && merged.imageAssetId) {
          merged.imageUrl = `/uploads/preupload/${merged.imageAssetId}.jpeg`;
        }
        if (!merged.audioUrl && merged.audioLibraryFilename) {
          merged.audioUrl = `/audio_library/${encodeURIComponent(merged.audioLibraryFilename)}`;
        }
        if (!merged.selectedSteps || ![3, 4, 8].includes(parseInt(merged.selectedSteps))) {
          merged.selectedSteps = 3;
        }
        if (!merged.selectedPreset || !['distill_bf16', 'distill_int8'].includes(merged.selectedPreset)) {
          merged.selectedPreset = 'distill_bf16';
        }
        if (!merged.stepBooster) merged.stepBooster = 'sage_attention';
        if (!merged.selectedResolution || merged.selectedResolution === 'auto') {
          merged.selectedResolution = '500p';
        }
        if (!merged.generationMode) {
          merged.generationMode = 'anchor_seamless';
        }
        if (!merged.numFrames) {
          merged.numFrames = 205;
        }
        
        let fallbackGender = '';
        try { fallbackGender = localStorage.getItem(`longcat_slot_${s.id}_gender`); } catch (e) {}
        if (fallbackGender === 'female' || fallbackGender === 'male') {
          merged.gender = fallbackGender;
        }

        if (merged.gender === 'female') {
          if (!merged.prompt || !merged.prompt.startsWith('Use the uploaded image exactly as the reference') || !merged.prompt.includes('woman')) {
            merged.prompt = FEMALE_POSITIVE_PROMPT;
          }
          if (!merged.negativePrompt || !merged.negativePrompt.includes('Aggressive speech, shouting, wide over-opened mouth')) {
            merged.negativePrompt = FEMALE_NEGATIVE_PROMPT;
          }
        } else {
          if (!merged.prompt || !merged.prompt.startsWith('Use the uploaded image exactly as the reference') || !merged.prompt.includes('man')) {
            merged.prompt = DEFAULT_POSITIVE_PROMPT;
          }
          if (!merged.negativePrompt || !merged.negativePrompt.includes('Aggressive speech, shouting, yelling')) {
            merged.negativePrompt = DEFAULT_NEGATIVE_PROMPT;
          }
        }
        cleanSlots.push(merged);
      }
      cleanSlots.sort((a, b) => a.id - b.id);
      studioState.slots = cleanSlots;
    }

    // Fallback: Ensure at least 1 slot exists
    if (!studioState.slots || studioState.slots.length === 0) {
      studioState.slots = [createSlot(1, 'Video 1')];
    }

    const savedActiveId = localStorage.getItem('longcat_active_slot_id');
    if (savedActiveId) {
      const parsedId = parseInt(savedActiveId);
      if (studioState.slots.some(s => s.id === parsedId)) {
        studioState.activeSlotId = parsedId;
      }
    }

    // Resume any active polling monitors
    studioState.slots.forEach(slot => {
      if (slot.taskId && (slot.status === 'running' || slot.status === 'queued')) {
        startSlotMonitor(slot);
      }
    });

  } catch (e) {
    console.error('State restore error:', e);
  }

  renderSlotTabs();
  populateDOMFromActiveSlot();
}

let serverStateSaveTimer = null;
function debouncedSyncServerState(lightSlots, activeSlotId) {
  if (serverStateSaveTimer) clearTimeout(serverStateSaveTimer);
  serverStateSaveTimer = setTimeout(async () => {
    try {
      await fetch('/api/studio_state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slots: lightSlots,
          activeSlotId: activeSlotId,
          updatedAt: Date.now()
        })
      });
    } catch (e) {
      console.warn('Failed to sync studio state to server:', e);
    }
  }, 350);
}

async function restoreMediaFromIndexedDBAndSyncQueue() {
  try {
    // 0. Synchronize Persistent Studio State from Server (Master source of truth across hard refreshes and tabs)
    try {
      const stateRes = await fetch('/api/studio_state');
      if (stateRes.ok) {
        const serverState = await stateRes.json();
        if (serverState && Array.isArray(serverState.slots) && serverState.slots.length > 0) {
          let hasMergedChanges = false;
          serverState.slots.forEach(serverSlot => {
            let localSlot = studioState.slots.find(ls => ls.id === serverSlot.id);
            if (!localSlot) {
              localSlot = createSlot(serverSlot.id, serverSlot.name || `Video ${serverSlot.id}`);
              studioState.slots.push(localSlot);
              hasMergedChanges = true;
            }

            // Authoritative properties from server
            const keysToSync = [
              'title', 'imageName', 'imageUrl', 'imageAssetId', 'imageDimensions', 'imageSizeMb',
              'audioName', 'audioUrl', 'audioAssetId', 'audioLibraryFilename', 'audioDuration', 'audioSizeMb',
              'detectedRatio', 'detectedResolution', 'detectedQualityLabel', 'detectedRatioTitle',
              'gender', 'detectedGender', 'prompt', 'negativePrompt', 'seed', 'selectedPreset',
              'selectedSteps', 'stepBooster', 'selectedResolution', 'selectedRatio', 'numFrames',
              'taskId', 'status', 'progress', 'stage', 'outputVideoUrl', 'outputFilename', 'fileSizeMb',
              'outputVideoUrl720p', 'outputFilename720p', 'fileSize720pMb', 'durationFormatted', 'generationTimeFormatted'
            ];
            keysToSync.forEach(k => {
              if (serverSlot[k] !== undefined && serverSlot[k] !== null && serverSlot[k] !== '') {
                if (localSlot[k] === undefined || localSlot[k] === null || localSlot[k] === '' ||
                    ['imageUrl', 'imageAssetId', 'audioUrl', 'audioAssetId', 'taskId', 'status', 'outputVideoUrl', 'imageName', 'audioName'].includes(k)) {
                  localSlot[k] = serverSlot[k];
                  hasMergedChanges = true;
                }
              }
            });

            if (!localSlot.imageUrl && localSlot.imageAssetId) {
              localSlot.imageUrl = `/uploads/preupload/${localSlot.imageAssetId}.jpeg`;
              hasMergedChanges = true;
            }
            if (!localSlot.audioUrl && localSlot.audioLibraryFilename) {
              localSlot.audioUrl = `/audio_library/${encodeURIComponent(localSlot.audioLibraryFilename)}`;
              hasMergedChanges = true;
            }

            // Asynchronously rehydrate imageDataUrl in background from imageUrl if missing
            if (localSlot.imageUrl && !localSlot.imageDataUrl && !localSlot._rehydrating) {
              localSlot._rehydrating = true;
              fetch(localSlot.imageUrl)
                .then(res => res.ok ? res.blob() : null)
                .then(blob => {
                  if (blob) {
                    localSlot.imageFile = blob;
                    const r = new FileReader();
                    r.onload = (e) => {
                      localSlot.imageDataUrl = e.target.result;
                      if (studioState.activeSlotId === localSlot.id) {
                        renderImageUI(localSlot);
                      }
                    };
                    r.readAsDataURL(blob);
                  }
                })
                .catch(() => {})
                .finally(() => { localSlot._rehydrating = false; });
            }
          });

          if (hasMergedChanges) {
            studioState.slots.sort((a, b) => a.id - b.id);
            renderSlotTabs();
            populateDOMFromActiveSlot();
            saveStudioState();
          }
        }
      }
    } catch (e) {
      console.warn('Server studio_state sync note:', e);
    }

    // 1. Asynchronously restore heavy media blobs from IndexedDB in background
    const db = await openStudioDB();
    if (db) {
      const dbSlots = await new Promise((resolve) => {
        try {
          const tx = db.transaction(DB_STORE, 'readonly');
          const store = tx.objectStore(DB_STORE);
          const req = store.getAll();
          req.onsuccess = () => resolve(req.result || []);
          req.onerror = () => resolve([]);
        } catch (err) {
          resolve([]);
        }
      });

      if (Array.isArray(dbSlots) && dbSlots.length > 0) {
        dbSlots.forEach(dbS => {
          const matched = studioState.slots.find(s => s.id === dbS.id);
          if (matched) {
            if (dbS.imageDataUrl && !matched.imageDataUrl) matched.imageDataUrl = dbS.imageDataUrl;
            if (dbS.audioDataUrl && !matched.audioDataUrl) matched.audioDataUrl = dbS.audioDataUrl;
          }
        });
        populateDOMFromActiveSlot();
      }
    }

    // 2. Dynamic queue sync on page load (Never drop active or queued jobs on refresh)
    const qRes = await fetch('/api/queue');
    if (qRes.ok) {
      const qData = await qRes.json();
      const rawActiveList = qData.active_tasks || (qData.active_task ? [qData.active_task] : []);
      const rawQueuedList = qData.queued_tasks || [];

      const activeList = rawActiveList;
      const queuedList = rawQueuedList;
      const allBusyTasks = [...activeList, ...queuedList];

      if (allBusyTasks.length > 0) {
        studioState.hasActiveBackendTask = (activeList.length > 0);
        const sortedActiveList = [...activeList].sort((a, b) => (b.progress || 0) - (a.progress || 0));

        sortedActiveList.forEach((at) => {
          let matchedSlot = studioState.slots.find(s => s.taskId === at.id);
          if (!matchedSlot && at.slot_name && at.slot_name !== 'Avatar Library') {
            matchedSlot = studioState.slots.find(s => s.name === at.slot_name);
          }
          if (!matchedSlot && at.slot_name && at.slot_name !== 'Avatar Library') {
            const m = at.slot_name.match(/\d+/);
            const slotNum = m ? parseInt(m[0]) : (studioState.slots.length + 1);
            matchedSlot = createSlot(slotNum, at.slot_name);
            studioState.slots.push(matchedSlot);
            studioState.slots.sort((a, b) => a.id - b.id);
          }
          if (matchedSlot) {
            matchedSlot.taskId = at.id;
            matchedSlot.status = 'running';
            matchedSlot.progress = at.progress || 0.0;
            matchedSlot.stage = at.stage || 'Denoising on GPU...';
            matchedSlot.taskData = at;
            matchedSlot.logs = at.logs || [];
            startSlotMonitor(matchedSlot);
            renderProgressUI(matchedSlot);
            if (matchedSlot.id === studioState.activeSlotId) {
              renderTerminalLogs(matchedSlot.logs || []);
            }
          }
        });

        queuedList.forEach((qt) => {
          let matchedSlot = studioState.slots.find(s => s.taskId === qt.id);
          if (!matchedSlot && qt.slot_name && qt.slot_name !== 'Avatar Library') {
            matchedSlot = studioState.slots.find(s => s.name === qt.slot_name);
          }
          if (!matchedSlot && qt.slot_name && qt.slot_name !== 'Avatar Library') {
            const m = qt.slot_name.match(/\d+/);
            const slotNum = m ? parseInt(m[0]) : (studioState.slots.length + 1);
            matchedSlot = createSlot(slotNum, qt.slot_name);
            studioState.slots.push(matchedSlot);
            studioState.slots.sort((a, b) => a.id - b.id);
          }
          if (matchedSlot) {
            matchedSlot.taskId = qt.id;
            matchedSlot.status = 'queued';
            matchedSlot.stage = 'In GPU Queue...';
            startSlotMonitor(matchedSlot);
          }
        });
      } else {
        studioState.hasActiveBackendTask = false;
      }

      renderSlotTabs();
      updateQueueHeaderBadge(qData);
    }
  } catch(e) {}
}

// ==========================================
// 12. Backend Health & Uptime
// ==========================================
async function checkBackendHealth() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      const data = await res.json();
      const gpuTag = $('gpuTag');
      if (gpuTag && data.gpu) gpuTag.textContent = data.gpu;

      const badge = $('engineStatusBadge');
      if (badge) badge.className = 'engine-status-badge online';

      if (data.uptime_seconds !== undefined) {
        studioState.serverStartTimeMs = Date.now() - (data.uptime_seconds * 1000);
        localStorage.setItem('longcat_server_session_start', studioState.serverStartTimeMs.toString());
      }

      appendLog(`[${getTimeString()}] Connected to ${data.engine} (${data.gpu})`, 'success');
    }
  } catch (e) {
    appendLog(`[${getTimeString()}] Backend connection pending...`, 'system');
  }
}

function initUptimeCounter() {
  const counter = $('uptimeCounter');
  if (!counter) return;

  let sessionStart = localStorage.getItem('longcat_server_session_start');
  if (!sessionStart) {
    sessionStart = Date.now().toString();
    localStorage.setItem('longcat_server_session_start', sessionStart);
  }
  studioState.serverStartTimeMs = parseInt(sessionStart) || Date.now();

  setInterval(() => {
    const startMs = studioState.serverStartTimeMs || parseInt(localStorage.getItem('longcat_server_session_start')) || Date.now();
    const sec = Math.max(0, Math.floor((Date.now() - startMs) / 1000));
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    
    if (h > 0) {
      counter.textContent = `${h < 10 ? '0' : ''}${h}h ${m < 10 ? '0' : ''}${m}m ${s < 10 ? '0' : ''}${s}s`;
    } else {
      counter.textContent = `${m < 10 ? '0' : ''}${m}m ${s < 10 ? '0' : ''}${s}s`;
    }
  }, 1000);
}

// Helpers
function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function getTimeString() {
  return new Date().toTimeString().split(' ')[0];
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ==========================================
// 13. Global Browser Audio Activation & MEI Unlocker
// ==========================================
let browserAudioUnlocked = false;
function unlockBrowserAudio() {
  if (browserAudioUnlocked) return;
  browserAudioUnlocked = true;
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) {
      const ctx = new AudioCtx();
      ctx.resume().then(() => ctx.close());
    }
  } catch (e) {}
}
['click', 'touchstart', 'mousedown', 'keydown'].forEach(evt => {
  window.addEventListener(evt, unlockBrowserAudio, { passive: true });
});
