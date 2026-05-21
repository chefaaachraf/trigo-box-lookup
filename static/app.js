'use strict';

// ── DOM refs ──────────────────────────────────────────────────────────────────
const scanInput        = document.getElementById('scan-input');
const inputWrap        = document.getElementById('input-wrap');
const resultCard       = document.getElementById('result-card');
const resultBadge      = document.getElementById('result-badge');
const resultRef        = document.getElementById('result-ref');
const resultUC         = document.getElementById('result-uc');
const resultDetail     = document.getElementById('result-detail');
const resultImg        = document.getElementById('result-img');
const imagePlaceholder = document.getElementById('image-placeholder');
const historyEmpty     = document.getElementById('history-empty');
const historyWrap      = document.getElementById('history-wrap');
const historyTbody     = document.getElementById('history-tbody');
const statusMsg        = document.getElementById('status-msg');
const kpiRefs          = document.getElementById('kpi-refs');
const kpiScans         = document.getElementById('kpi-scans');
const kpiRate          = document.getElementById('kpi-rate');
const scanFlash        = document.getElementById('scan-flash');
const progressBar      = document.getElementById('reading-progress');
const exportBtn        = document.getElementById('export-btn');
const clearHistoryBtn  = document.getElementById('clear-history-btn');
const histSearch       = document.getElementById('hist-search');
const histStatus       = document.getElementById('hist-status');
const histDate         = document.getElementById('hist-date');
const histCount        = document.getElementById('hist-count');
const soundBtn         = document.getElementById('sound-btn');
const soundOnIcon      = document.getElementById('sound-on-icon');
const soundOffIcon     = document.getElementById('sound-off-icon');

// Onglets et vues
const viewScan   = document.getElementById('view-scan');
const viewBase   = document.getElementById('view-base');
const viewSaisie = document.getElementById('view-saisie');
const tabScan    = document.getElementById('tab-scan');
const tabBase    = document.getElementById('tab-base');
const tabSaisie  = document.getElementById('tab-saisie');

// Base refs
const baseSearch = document.getElementById('base-search');
const baseTbody  = document.getElementById('base-tbody');
const baseEmpty  = document.getElementById('base-empty');
const baseWrap   = document.getElementById('base-wrap');
const baseCount  = document.getElementById('base-count');

// Saisie manuelle
const addForm              = document.getElementById('add-form');
const addRefInput          = document.getElementById('add-ref');
const addUcInput           = document.getElementById('add-uc');
const addDescInput         = document.getElementById('add-desc');
const addEmplacementInput  = document.getElementById('add-emplacement');
const addFeedback          = document.getElementById('add-feedback');
const manualEmpty          = document.getElementById('manual-empty');
const manualWrap           = document.getElementById('manual-wrap');
const manualTbody          = document.getElementById('manual-tbody');
const addPhotoInput        = document.getElementById('add-photo');
const photoDrop            = document.getElementById('photo-drop');
const photoPreviewWrap     = document.getElementById('photo-preview-wrap');
const photoPreview         = document.getElementById('photo-preview');
const photoPlaceholder     = document.getElementById('photo-placeholder');
const addPlacementInput    = document.getElementById('add-placement-photo');
const placementDrop        = document.getElementById('placement-drop');
const placementPreviewWrap = document.getElementById('placement-preview-wrap');
const placementPlaceholder = document.getElementById('placement-placeholder');

// Emplacement dans le bac (vue scan)
const emplacementSection = document.getElementById('emplacement-section');
const emplacementText    = document.getElementById('emplacement-text');
const emplacementGallery = document.getElementById('emplacement-gallery');

// Caméra
const cameraBtn    = document.getElementById('camera-btn');
const cameraModal  = document.getElementById('camera-modal');
const cameraClose  = document.getElementById('camera-close');
const cameraVideo  = document.getElementById('camera-video');
const cameraStatus = document.getElementById('camera-status');
const cameraSelect = document.getElementById('camera-select');

// ── Constantes ────────────────────────────────────────────────────────────────
const STATUS_LABELS = {
  found:      'TROUVÉ',
  error:      'ERREUR',
  incomplete: 'INCOMPLET',
  idle:       'EN ATTENTE',
};

let _scanCount   = 0;
let _foundCount  = 0;
let _historyCache = [];
let _soundOn     = true;

// ── Utilitaires ───────────────────────────────────────────────────────────────
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function flash(type) {
  scanFlash.className = type === 'found' ? 'flash-ok' : 'flash-nok';
  setTimeout(() => { scanFlash.className = ''; }, 400);
}

function animateProgress(pct) {
  progressBar.style.width = pct + '%';
  if (pct >= 100) setTimeout(() => { progressBar.style.width = '0%'; }, 600);
}

function showFeedback(msg, ok) {
  addFeedback.textContent = msg;
  addFeedback.className   = `add-feedback ${ok ? 'ok' : 'nok'}`;
  addFeedback.classList.remove('hidden');
  setTimeout(() => addFeedback.classList.add('hidden'), 4000);
}

// ── Sons ──────────────────────────────────────────────────────────────────────
let _audioCtx = null;

function getAudioCtx() {
  if (!_audioCtx) _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  return _audioCtx;
}

function beep(freq, duration, type = 'sine', vol = 0.25) {
  if (!_soundOn) return;
  try {
    const ctx  = getAudioCtx();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (_) {}
}

function playOk() {
  beep(880, 0.12);
  setTimeout(() => beep(1320, 0.18), 100);
}

function playError() {
  beep(200, 0.35, 'sawtooth', 0.2);
}

function playWarn() {
  beep(550, 0.15);
  setTimeout(() => beep(440, 0.25), 130);
}

// Toggle son
soundBtn.addEventListener('click', () => {
  _soundOn = !_soundOn;
  soundBtn.classList.toggle('active', _soundOn);
  soundOnIcon.classList.toggle('hidden', !_soundOn);
  soundOffIcon.classList.toggle('hidden', _soundOn);
});

// ── Navigation par onglets ────────────────────────────────────────────────────
const VIEWS = { scan: viewScan, base: viewBase, saisie: viewSaisie };
const TABS  = { scan: tabScan,  base: tabBase,  saisie: tabSaisie  };

function switchTab(name) {
  Object.keys(VIEWS).forEach(k => {
    VIEWS[k].style.display = k === name ? '' : 'none';
    TABS[k].classList.toggle('active', k === name);
  });
  if (name === 'scan')   { scanInput.focus(); }
  if (name === 'base')   { loadBase(); baseSearch.focus(); }
  if (name === 'saisie') { loadManual(); addRefInput.focus(); }
}

tabScan.addEventListener('click',   e => { e.preventDefault(); switchTab('scan'); });
tabBase.addEventListener('click',   e => { e.preventDefault(); switchTab('base'); });
tabSaisie.addEventListener('click', e => { e.preventDefault(); switchTab('saisie'); });

// ── Scan / résultat ───────────────────────────────────────────────────────────
function setResult(data) {
  const status = data.status || 'idle';
  resultCard.className    = `card result-card ${status}`;
  resultBadge.textContent = STATUS_LABELS[status] || status.toUpperCase();
  resultBadge.className   = `badge ${status}`;
  resultRef.textContent   = data.ref ? `Réf : ${data.ref}` : '';
  resultUC.textContent    = data.uc || data.message || 'En attente de scan…';
  resultUC.className      = `result-uc ${status}`;
  resultDetail.textContent = data.message || '';

  if (data.image_url) {
    imagePlaceholder.classList.add('hidden');
    resultImg.src = data.image_url;
    resultImg.classList.remove('hidden');
  } else {
    imagePlaceholder.classList.remove('hidden');
    resultImg.classList.add('hidden');
    resultImg.src = '';
  }

  // ── Emplacement + galerie
  const urls = data.placement_image_urls || [];
  if (data.emplacement || urls.length) {
    emplacementSection.classList.remove('hidden');
    emplacementText.textContent = data.emplacement || '';
    renderPlacementGallery(urls, data.ref);
  } else {
    emplacementSection.classList.add('hidden');
    emplacementText.textContent = '';
    emplacementGallery.innerHTML = '';
    emplacementGallery.classList.add('hidden');
  }
}

function updateRate() {
  kpiRate.textContent = _scanCount === 0
    ? '—'
    : Math.round((_foundCount / _scanCount) * 100) + '%';
}

const _today = new Date().toLocaleDateString('fr-FR');

function formatDateTime(row) {
  // Affiche "HH:MM:SS" si c'est aujourd'hui, "JJ/MM/AAAA HH:MM:SS" sinon
  if (row.date && row.date !== _today) return `${row.date} ${row.time || ''}`;
  return row.time || '';
}

function renderHistory(items) {
  _historyCache = items;
  if (!items.length) {
    historyEmpty.classList.remove('hidden');
    historyWrap.classList.add('hidden');
    return;
  }
  historyEmpty.classList.add('hidden');
  historyWrap.classList.remove('hidden');

  historyTbody.innerHTML = items.map(row => {
    const ref   = escapeHtml(row.ref  || row.raw || '—');
    const uc    = escapeHtml(row.uc   || '—');
    const label = STATUS_LABELS[row.status] || (row.status || '').toUpperCase();
    const dt    = escapeHtml(formatDateTime(row));
    return `<tr>
      <td style="white-space:nowrap">${dt}</td>
      <td>${ref}</td>
      <td class="uc-cell">${uc}</td>
      <td><span class="status-badge ${escapeHtml(row.status || '')}">${label}</span></td>
    </tr>`;
  }).join('');
}

async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    kpiRefs.textContent   = d.ref_count ?? '—';
    kpiScans.textContent  = d.scan_count ?? 0;
    _scanCount            = d.scan_count ?? 0;
    statusMsg.textContent = `Prêt — ${d.ref_count} références chargées`;
  } catch {
    statusMsg.textContent = 'Erreur de connexion au serveur';
  }
}

// Remplir le sélecteur de date avec aujourd'hui (valeur lisible)
histDate.options[1].value = new Date().toLocaleDateString('fr-FR');

let _histDebounce = null;

function getHistFilters() {
  const params = new URLSearchParams({ limit: 200 });
  const q      = histSearch.value.trim();
  const status = histStatus.value;
  const date   = histDate.value;
  if (q)      params.set('q', q);
  if (status) params.set('status', status);
  if (date)   params.set('date', date);
  return params;
}

async function loadHistory(fromFilter = false) {
  try {
    const r     = await fetch(`/api/history?${getHistFilters()}`);
    const items = await r.json();
    renderHistory(items);

    // Mettre à jour le compteur de filtre
    const total = _historyCache.length;
    if (fromFilter || histSearch.value || histStatus.value || histDate.value) {
      histCount.textContent = `${items.length} résultat(s)`;
    } else {
      histCount.textContent = items.length ? `${items.length} entrée(s)` : '';
    }

    // Recalculer taux de succès uniquement sur chargement initial (sans filtre)
    if (!fromFilter && !histSearch.value && !histStatus.value && !histDate.value) {
      _foundCount = items.filter(r => r.status === 'found').length;
      updateRate();
    }
  } catch { /* silencieux */ }
}

// Filtres : déclenchement
histSearch.addEventListener('input', () => {
  clearTimeout(_histDebounce);
  _histDebounce = setTimeout(() => loadHistory(true), 250);
});
histStatus.addEventListener('change', () => loadHistory(true));
histDate.addEventListener('change',   () => loadHistory(true));

// ── Vider l'historique ────────────────────────────────────────────────────────
clearHistoryBtn.addEventListener('click', async () => {
  if (!_historyCache.length) return;
  if (!confirm(`Vider les ${_historyCache.length} entrées de l'historique ? Cette action est irréversible.`)) return;
  try {
    await fetch('/api/history', { method: 'DELETE' });
    _historyCache = [];
    _scanCount = 0;
    _foundCount = 0;
    kpiScans.textContent = 0;
    updateRate();
    histCount.textContent = '';
    renderHistory([]);
    loadStats();
    statusMsg.textContent = 'Historique vidé';
  } catch {
    statusMsg.textContent = 'Erreur lors de la suppression';
  }
});

async function submitScan() {
  const raw = scanInput.value.trim();
  scanInput.value = '';
  if (!raw) return;

  inputWrap.classList.add('scanning');
  animateProgress(60);
  statusMsg.textContent = `Recherche : ${raw}…`;

  try {
    const r    = await fetch(`/api/lookup?ref=${encodeURIComponent(raw)}`);
    const data = await r.json();

    animateProgress(100);
    inputWrap.classList.remove('scanning');
    setResult(data);
    flash(data.status);

    _scanCount++;
    if (data.status === 'found') {
      _foundCount++;
      playOk();
      statusMsg.textContent = `✓  ${data.ref}  →  ${data.uc}`;
    } else if (data.status === 'error') {
      playError();
      statusMsg.textContent = `✗  Référence non reconnue dans la base`;
    } else {
      playWarn();
      statusMsg.textContent = `⚠  ${data.ref}  →  UC non défini`;
    }

    kpiScans.textContent = _scanCount;
    updateRate();
    loadHistory();
  } catch {
    animateProgress(0);
    inputWrap.classList.remove('scanning');
    statusMsg.textContent = 'Erreur réseau — serveur inaccessible';
  }
}

scanInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') submitScan();
});

document.addEventListener('click', e => {
  if (viewScan.style.display !== 'none' && e.target !== scanInput
      && !cameraModal.contains(e.target)) {
    scanInput.focus();
  }
});

// ── Export CSV ────────────────────────────────────────────────────────────────
exportBtn.addEventListener('click', () => {
  if (!_historyCache.length) {
    statusMsg.textContent = 'Aucun scan à exporter';
    return;
  }

  const sep = ';';
  const headers = ['Heure', 'Référence scannée', 'Référence normalisée', 'UC', 'Statut'];
  const rows = _historyCache.map(r => [
    r.time  || '',
    r.raw   || '',
    r.ref   || '',
    r.uc    || '',
    STATUS_LABELS[r.status] || r.status || '',
  ]);

  const csv = [headers, ...rows]
    .map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(sep))
    .join('\r\n');

  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const now  = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', 'h');
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `boxlookup_session_${now}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  statusMsg.textContent = `✓  Export CSV — ${_historyCache.length} ligne(s)`;
});

// ── Base des références ───────────────────────────────────────────────────────
let _baseDebounce = null;

async function loadBase(q = '') {
  try {
    const r    = await fetch(`/api/refs?q=${encodeURIComponent(q)}`);
    const data = await r.json();
    renderBase(data);
  } catch { /* silencieux */ }
}

function renderBase(items) {
  baseCount.textContent = `${items.length} résultat(s)`;
  if (!items.length) {
    baseEmpty.classList.remove('hidden');
    baseWrap.classList.add('hidden');
    return;
  }
  baseEmpty.classList.add('hidden');
  baseWrap.classList.remove('hidden');

  baseTbody.innerHTML = items.map((row, i) => `<tr>
    <td style="color:var(--muted-light);font-size:.72rem">${i + 1}</td>
    <td><code style="font-size:.78rem">${escapeHtml(row.ref)}</code></td>
    <td class="uc-cell">${escapeHtml(row.uc || '—')}</td>
  </tr>`).join('');
}

baseSearch.addEventListener('input', () => {
  clearTimeout(_baseDebounce);
  _baseDebounce = setTimeout(() => loadBase(baseSearch.value.trim()), 220);
});

// ── Saisie manuelle — photo ───────────────────────────────────────────────────
function setPhotoPreview(file) {
  const url = URL.createObjectURL(file);
  photoPreview.src = url;
  photoPreviewWrap.classList.remove('hidden');
  photoPlaceholder.classList.add('hidden');
}

function clearPhotoPreview() {
  photoPreview.src = '';
  photoPreviewWrap.classList.add('hidden');
  photoPlaceholder.classList.remove('hidden');
}

addPhotoInput.addEventListener('change', () => {
  if (addPhotoInput.files[0]) setPhotoPreview(addPhotoInput.files[0]);
  else clearPhotoPreview();
});

photoDrop.addEventListener('dragover', e => { e.preventDefault(); photoDrop.classList.add('dragover'); });
photoDrop.addEventListener('dragleave', () => photoDrop.classList.remove('dragover'));
photoDrop.addEventListener('drop', e => {
  e.preventDefault();
  photoDrop.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    const dt = new DataTransfer();
    dt.items.add(file);
    addPhotoInput.files = dt.files;
    setPhotoPreview(file);
  }
});

// ── Photos d'emplacement (multi-fichiers) ────────────────────────────────────
let _placementFiles = [];

function _renderPlacementForm() {
  if (!_placementFiles.length) {
    placementPreviewWrap.classList.add('hidden');
    placementPlaceholder.classList.remove('hidden');
    return;
  }
  placementPlaceholder.classList.add('hidden');
  placementPreviewWrap.classList.remove('hidden');
  placementPreviewWrap.innerHTML = _placementFiles.map((f, i) => {
    const url = URL.createObjectURL(f);
    return `<div class="placement-thumb">
      <img src="${url}" alt="Photo ${i + 1}">
      <button type="button" class="placement-thumb-del" data-idx="${i}" title="Supprimer">✕</button>
    </div>`;
  }).join('');
  placementPreviewWrap.querySelectorAll('.placement-thumb-del').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      _placementFiles.splice(parseInt(btn.dataset.idx), 1);
      _renderPlacementForm();
    });
  });
}

function clearPlacementPreview() {
  _placementFiles = [];
  _renderPlacementForm();
}

function _addPlacementFiles(fileList) {
  for (const f of fileList) {
    if (f.type.startsWith('image/')) _placementFiles.push(f);
  }
  _renderPlacementForm();
}

addPlacementInput.addEventListener('change', () => {
  if (addPlacementInput.files.length) _addPlacementFiles(addPlacementInput.files);
  addPlacementInput.value = '';
});

placementDrop.addEventListener('dragover', e => { e.preventDefault(); placementDrop.classList.add('dragover'); });
placementDrop.addEventListener('dragleave', () => placementDrop.classList.remove('dragover'));
placementDrop.addEventListener('drop', e => {
  e.preventDefault();
  placementDrop.classList.remove('dragover');
  _addPlacementFiles(e.dataTransfer.files);
});

// ── Galerie emplacement (vue scan) ────────────────────────────────────────────
function renderPlacementGallery(urls, ref) {
  if (!urls.length) {
    emplacementGallery.classList.add('hidden');
    emplacementGallery.innerHTML = '';
    return;
  }
  emplacementGallery.classList.remove('hidden');
  emplacementGallery.innerHTML = urls.map((url, i) => {
    const filename = url.split('/').pop();
    return `<div class="placement-gallery-item">
      <img src="${url}" alt="Photo emplacement ${i + 1}" loading="lazy"
           onclick="window.open('${url}','_blank')" title="Cliquer pour agrandir">
      <button class="placement-gallery-del" data-ref="${escapeHtml(ref || '')}"
              data-file="${escapeHtml(filename)}" title="Supprimer cette photo">✕</button>
    </div>`;
  }).join('');
  emplacementGallery.querySelectorAll('.placement-gallery-del').forEach(btn => {
    btn.addEventListener('click', () => _deletePlacementPhoto(btn.dataset.ref, btn.dataset.file, btn));
  });
}

async function _deletePlacementPhoto(ref, filename, btn) {
  if (!confirm(`Supprimer la photo "${filename}" ?`)) return;
  try {
    const r = await fetch(`/api/delete-placement/${encodeURIComponent(ref)}/${encodeURIComponent(filename)}`,
                          { method: 'DELETE' });
    const d = await r.json();
    if (r.ok) renderPlacementGallery(d.placement_image_urls || [], ref);
  } catch { /* silencieux */ }
}

// ── Saisie manuelle — formulaire ──────────────────────────────────────────────
addForm.addEventListener('submit', async e => {
  e.preventDefault();
  const ref         = addRefInput.value.trim();
  const uc          = addUcInput.value.trim();
  const desc        = addDescInput.value.trim();
  const emplacement = addEmplacementInput.value.trim();

  if (!ref || !uc) { showFeedback('Référence et UC sont obligatoires.', false); return; }

  try {
    const r = await fetch('/api/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ref, uc, desc, emplacement }),
    });
    const d = await r.json();

    if (!r.ok) { showFeedback(d.message || 'Erreur serveur', false); return; }

    // Upload photo emballage
    const photoFile = addPhotoInput.files[0];
    if (photoFile) {
      const fd = new FormData();
      fd.append('uc', uc);
      fd.append('file', photoFile);
      await fetch('/api/upload-image', { method: 'POST', body: fd });
    }

    // Upload photos d'emplacement (une par une)
    for (const placementFile of _placementFiles) {
      const fd = new FormData();
      fd.append('ref', ref);
      fd.append('file', placementFile);
      await fetch('/api/upload-placement', { method: 'POST', body: fd });
    }

    const nPhotos = _placementFiles.length;
    showFeedback(
      `${d.status === 'updated' ? 'Mise à jour' : 'Ajoutée'} — ${ref} → ${uc}` +
      (nPhotos ? `  (${nPhotos} photo${nPhotos > 1 ? 's' : ''} emplacement)` : ''),
      true
    );
    addRefInput.value = addUcInput.value = addDescInput.value = addEmplacementInput.value = '';
    addPhotoInput.value = '';
    clearPhotoPreview();
    clearPlacementPreview();
    addRefInput.focus();
    loadManual();
    loadStats();
  } catch {
    showFeedback('Erreur réseau — serveur inaccessible', false);
  }
});

function renderManual(items) {
  if (!items.length) {
    manualEmpty.classList.remove('hidden');
    manualWrap.classList.add('hidden');
    return;
  }
  manualEmpty.classList.add('hidden');
  manualWrap.classList.remove('hidden');

  manualTbody.innerHTML = items.map(row => `<tr>
    <td><code style="font-size:.78rem">${escapeHtml(row.ref)}</code></td>
    <td class="uc-cell">${escapeHtml(row.uc)}</td>
    <td style="color:var(--muted);font-size:.76rem">${escapeHtml(row.emplacement || '—')}</td>
    <td style="color:var(--muted);font-size:.76rem">${escapeHtml(row.desc || '—')}</td>
    <td><button class="btn-del" data-ref="${escapeHtml(row.ref)}">✕</button></td>
  </tr>`).join('');

  manualTbody.querySelectorAll('.btn-del').forEach(btn => {
    btn.addEventListener('click', () => deleteManual(btn.dataset.ref));
  });
}

async function loadManual() {
  try {
    const r = await fetch('/api/manual');
    renderManual(await r.json());
  } catch { /* silencieux */ }
}

async function deleteManual(ref) {
  try {
    await fetch(`/api/manual/${encodeURIComponent(ref)}`, { method: 'DELETE' });
    loadManual();
    loadStats();
    statusMsg.textContent = `Entrée supprimée : ${ref}`;
  } catch {
    statusMsg.textContent = 'Erreur lors de la suppression';
  }
}

// ── QR code / accès réseau ────────────────────────────────────────────────────
const qrBtn   = document.getElementById('qr-btn');
const qrModal = document.getElementById('qr-modal');
const qrClose = document.getElementById('qr-close');
const qrImg   = document.getElementById('qr-img');
const qrUrl   = document.getElementById('qr-url');

qrBtn.addEventListener('click', async () => {
  qrModal.classList.remove('hidden');
  // QR généré côté serveur — pas de dépendance CDN
  qrImg.src = `/api/qrcode.png?t=${Date.now()}`;
  try {
    const r    = await fetch('/api/network-info');
    const info = await r.json();
    qrUrl.textContent = info.url;
  } catch {
    qrUrl.textContent = 'Adresse réseau indisponible';
  }
});

qrClose.addEventListener('click', () => qrModal.classList.add('hidden'));
qrModal.addEventListener('click', e => { if (e.target === qrModal) qrModal.classList.add('hidden'); });

// ── Documentation ─────────────────────────────────────────────────────────────
const docBtn   = document.getElementById('doc-btn');
const docModal = document.getElementById('doc-modal');
const docClose = document.getElementById('doc-close');

docBtn.addEventListener('click', () => docModal.classList.remove('hidden'));
docClose.addEventListener('click', () => docModal.classList.add('hidden'));
docModal.addEventListener('click', e => { if (e.target === docModal) docModal.classList.add('hidden'); });

// ── Scanner caméra ────────────────────────────────────────────────────────────
let _zxing   = null;
let _scanning = false;

function setCameraStatus(msg, type) {
  cameraStatus.textContent = msg;
  cameraStatus.className   = `camera-status${type ? ' ' + type : ''}`;
}

async function openCamera() {
  cameraModal.classList.remove('hidden');
  setCameraStatus('Initialisation de la caméra…');

  if (typeof ZXing === 'undefined') {
    setCameraStatus('Bibliothèque de scan non disponible (vérifiez la connexion internet).', 'err');
    return;
  }

  try {
    _zxing = new ZXing.BrowserMultiFormatReader();
    const devices = await _zxing.listVideoInputDevices();

    if (!devices.length) { setCameraStatus('Aucune caméra détectée.', 'err'); return; }

    if (devices.length > 1) {
      cameraSelect.innerHTML = devices.map((d, i) =>
        `<option value="${escapeHtml(d.deviceId)}">${escapeHtml(d.label || 'Caméra ' + (i + 1))}</option>`
      ).join('');
      cameraSelect.selectedIndex = devices.length - 1;
      cameraSelect.classList.remove('hidden');
    } else {
      cameraSelect.classList.add('hidden');
    }

    startZxing(cameraSelect.value || devices[0].deviceId);
  } catch (err) {
    setCameraStatus(`Erreur caméra : ${err.message}`, 'err');
  }
}

function startZxing(deviceId) {
  _scanning = true;
  setCameraStatus('Pointez la caméra vers le code-barre GALIA…');

  _zxing.decodeFromVideoDevice(deviceId || undefined, cameraVideo, (result, err) => {
    if (!_scanning) return;
    if (result) {
      _scanning = false;
      const text = result.getText();
      setCameraStatus(`✓ Détecté : ${text}`, 'ok');
      setTimeout(() => {
        closeCamera();
        scanInput.value = text;
        submitScan();
      }, 400);
      return;
    }
    if (err && !(err instanceof ZXing.NotFoundException)) {
      setCameraStatus(`Erreur : ${err.message}`, 'err');
    }
  });
}

function closeCamera() {
  _scanning = false;
  if (_zxing) { try { _zxing.reset(); } catch (_) {} _zxing = null; }
  cameraModal.classList.add('hidden');
  cameraSelect.classList.add('hidden');
  cameraSelect.innerHTML = '';
}

cameraBtn.addEventListener('click', openCamera);
cameraClose.addEventListener('click', closeCamera);
cameraModal.addEventListener('click', e => { if (e.target === cameraModal) closeCamera(); });
cameraSelect.addEventListener('change', () => {
  if (_zxing) { try { _zxing.reset(); } catch (_) {} }
  startZxing(cameraSelect.value);
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !cameraModal.classList.contains('hidden')) closeCamera();
});

// ── Init ──────────────────────────────────────────────────────────────────────
loadStats();
loadHistory();
scanInput.focus();

// Charger l'URL réseau pour le QR left-column
(async () => {
  try {
    const r    = await fetch('/api/network-info');
    const info = await r.json();
    const el   = document.getElementById('qr-left-url');
    if (el) el.textContent = info.url;
  } catch { /* silencieux */ }
})();

const qrLeftImg     = document.getElementById('qr-left-img');
const qrLeftRefresh = document.getElementById('qr-left-refresh');
if (qrLeftRefresh && qrLeftImg) {
  qrLeftRefresh.addEventListener('click', () => {
    qrLeftImg.src = `/api/qrcode.png?t=${Date.now()}`;
  });
}
