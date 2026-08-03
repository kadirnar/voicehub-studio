import {
  getLocale,
  getLocalePreference,
  localizeTree,
  setLocalePreference,
  t,
} from './i18n.js';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const ICONS = {
  sparkles: '<path d="m12 3 .8 2.7a4.8 4.8 0 0 0 3.3 3.3l2.9.9-2.9.9a4.8 4.8 0 0 0-3.3 3.3L12 17l-.9-2.9a4.8 4.8 0 0 0-3.3-3.3L5 10l2.8-.9a4.8 4.8 0 0 0 3.3-3.3L12 3Z"/><path d="m18 15 .4 1.2a2.1 2.1 0 0 0 1.4 1.4l1.2.4-1.2.4a2.1 2.1 0 0 0-1.4 1.4L18 21l-.4-1.2a2.1 2.1 0 0 0-1.4-1.4L15 18l1.2-.4a2.1 2.1 0 0 0 1.4-1.4L18 15Z"/>',
  voices: '<path d="M12 13a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z"/><path d="M5 21a7 7 0 0 1 14 0"/><path d="M19 5.5a3 3 0 0 1 0 5.5M21 15.5a5.5 5.5 0 0 1 2 4.2"/>',
  waveform: '<path d="M3 12h2l1.5-5 3 10 3-14 3 18 2.5-12 2 6 1.2-3H23"/>',
  blocks: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3"/><path d="M1 14h6M9 8h6M17 16h6"/>',
  queue: '<path d="M4 6h16M4 12h16M4 18h10"/><circle cx="20" cy="18" r="2"/>',
  settings: '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5v13Z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  play: '<path d="m8 5 11 7-11 7V5Z"/>',
  pause: '<path d="M9 5H6v14h3V5ZM18 5h-3v14h3V5Z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
  mic: '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5M4 20h16"/>',
  download: '<path d="M12 4v12M7 11l5 5 5-5M4 20h16"/>',
  trash: '<path d="M4 7h16M9 3h6l1 4H8l1-4ZM7 7l1 14h8l1-14M10 11v6M14 11v6"/>',
  star: '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z"/>',
  clone: '<rect x="8" y="8" width="12" height="12" rx="3"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
  wand: '<path d="m15 4 5 5L8 21H3v-5L15 4Z"/><path d="m13 6 5 5M5 4v3M3.5 5.5h3M20 16v4M18 18h4"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  edit: '<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4L16.5 3.5Z"/>',
  x: '<path d="m6 6 12 12M18 6 6 18"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
  warning: '<path d="M12 3 2.5 20h19L12 3Z"/><path d="M12 9v5M12 17h.01"/>',
  cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3M10 10h4v4h-4z"/>',
  gpu: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="12" r="3"/><path d="M15 9h3M15 12h3M15 15h3"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>',
  folder: '<path d="M3 6h7l2 2h9v11H3V6Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  filter: '<path d="M4 5h16l-6 7v6l-4 2v-8L4 5Z"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 8a7 7 0 0 1 11.4-2L20 8M4 16l2.5 2a7 7 0 0 0 11.4-2"/>',
  scissors: '<circle cx="6" cy="7" r="3"/><circle cx="6" cy="17" r="3"/><path d="m8.5 8.5 12 8.5M8.5 15.5 20 7"/>',
  volume: '<path d="M5 10H2v4h3l4 4V6l-4 4ZM13 9a4 4 0 0 1 0 6M16 6a8 8 0 0 1 0 12"/>',
  magic: '<path d="M4 20 20 4M14 4l6 6M5 6h4M7 4v4M16 16h5M18.5 13.5v5"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
  external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 13v7H4V6h7"/>',
  terminal: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 15h4"/>',
  copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
  redo: '<path d="M20 7v6h-6M20 13l-4-4a7 7 0 1 0 1 10"/>',
  activity: '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
  save: '<path d="M4 4h14l2 2v14H4V4Z"/><path d="M8 4v6h8V4M8 20v-6h8v6"/>',
};

function icon(name, cls = '') {
  const body = ICONS[name] || ICONS.sparkles;
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
}

function hydrateIcons(root = document) {
  $$('[data-icon]', root).forEach((node) => {
    node.innerHTML = icon(node.dataset.icon);
  });
}

const ROUTES = {
  generate: ['Generate', 'Create speech with any VoiceHub model'],
  voices: ['Voices', 'Clone, design, and organize reusable voices'],
  editor: ['Audio editor', 'Cut, clean, transform, and combine audio'],
  models: ['Model library', 'Explore every TTS provider registered by VoiceHub'],
  training: ['Fine-tune', 'Train supported model families on your own dataset'],
  queue: ['Job queue', 'Monitor inference, editing, loading, and training'],
  settings: ['Settings', 'Compute, output, storage, and application defaults'],
};

const DEMO_MODELS = [
  ['qwen3tts', 'Qwen3-TTS', 'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice', ['voice-cloning', 'voice-design', 'expressive-speech']],
  ['chatterbox', 'Chatterbox', 'ResembleAI/chatterbox', ['voice-cloning', 'expressive-speech']],
  ['f5tts', 'F5-TTS', 'SWivid/F5-TTS', ['voice-cloning', 'multilingual']],
  ['kokoro', 'Kokoro', 'hexgrad/Kokoro-82M', ['multilingual', 'preset-voices']],
  ['xtts', 'XTTS v2', 'coqui/XTTS-v2', ['voice-cloning', 'multilingual']],
  ['parlertts', 'Parler-TTS', 'parler-tts/parler-tts-mini-v1', ['voice-design', 'prompted-style']],
].map(([model_type, display_name, default_checkpoint, capabilities]) => ({
  model_type, display_name, default_checkpoint, capabilities, architecture: 'VoiceHub adapter',
  installed: false, can_clone: capabilities.includes('voice-cloning'),
  can_design: capabilities.includes('voice-design') || capabilities.includes('prompted-style'),
  can_style: capabilities.includes('expressive-speech') || capabilities.includes('prompted-style'),
}));

const CHECKPOINT_VARIANTS = {
  qwen3tts: {
    synthesize: 'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice',
    clone: 'Qwen/Qwen3-TTS-12Hz-0.6B-Base',
    design: 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',
    choices: [
      'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice',
      'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice',
      'Qwen/Qwen3-TTS-12Hz-0.6B-Base',
      'Qwen/Qwen3-TTS-12Hz-1.7B-Base',
      'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',
    ],
  },
};

const DEFAULT_SCRIPTS = {
  en: 'Welcome to VoiceHub Studio. This voice was generated locally with full control over the model and delivery.',
  tr: 'VoiceHub Studio\'ya hoş geldiniz. Bu ses, model ve anlatım üzerinde tam denetimle yerel olarak üretildi.',
};

const TURKISH_DEFAULT = {
  model_type: 'supertonic',
  checkpoint: 'Supertone/supertonic-3',
  language: 'tr',
};

const state = {
  route: location.hash.slice(1) in ROUTES ? location.hash.slice(1) : 'generate',
  online: false,
  health: null,
  models: [],
  schema: null,
  schemaLoading: false,
  voices: [],
  assets: [],
  generations: [],
  jobs: [],
  training: [],
  projects: [],
  settings: {},
  system: null,
  runtime: null,
  selectedModel: null,
  generationMode: 'synthesize',
  generationText: DEFAULT_SCRIPTS[getLocale()],
  selectedVoiceId: null,
  checkpointOverride: null,
  selectedGenerationId: null,
  modelFilter: 'all',
  modelSearch: '',
  voiceSearch: '',
  voiceFilter: 'all',
  queueFilter: 'all',
  settingsTab: 'compute',
  editor: { assetId: null, peaks: null, start: 0, end: 0, dragging: false, operations: [] },
  refreshTimer: null,
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
}

function attr(value) { return escapeHtml(value); }
function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
function truncate(value, length = 84) {
  const text = String(value ?? '');
  return text.length > length ? `${text.slice(0, length - 1)}…` : text;
}
function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(getLocale() === 'tr' ? 'tr-TR' : undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}
function formatDuration(seconds) {
  if (seconds == null || !Number.isFinite(Number(seconds))) return '—';
  const total = Math.max(0, Number(seconds));
  const minutes = Math.floor(total / 60);
  const rest = total - minutes * 60;
  return `${minutes}:${rest.toFixed(2).padStart(5, '0')}`;
}
function formatBytes(bytes) {
  if (bytes == null) return '—';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = Number(bytes); let index = 0;
  while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1; }
  return `${value.toFixed(index > 1 ? 1 : 0)} ${units[index]}`;
}
function slugLabel(value) {
  const label = String(value ?? '').replaceAll('_', ' ').replaceAll('-', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  return t(label);
}

function syncDefaultScript() {
  if (!state.generationText || Object.values(DEFAULT_SCRIPTS).includes(state.generationText)) {
    state.generationText = DEFAULT_SCRIPTS[getLocale()];
  }
}
function initials(name) {
  return String(name || 'V').split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
}
function currentModel() {
  return state.models.find((model) => model.model_type === state.selectedModel) || state.models[0] || null;
}
function currentAsset() {
  return state.assets.find((asset) => asset.id === state.editor.assetId) || null;
}
function currentGeneration() {
  return state.generations.find((item) => item.id === state.selectedGenerationId) || state.generations[0] || null;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...(options.headers || {}) },
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = Array.isArray(payload.detail)
        ? payload.detail.map((item) => item.msg).join(', ')
        : payload.detail || detail;
    } catch (_) { /* response was not JSON */ }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

async function loadWorkspace({ quiet = false } = {}) {
  try {
    const [health, models, voices, assets, generations, jobs, training, settings, system, runtime] = await Promise.all([
      api('/api/health'), api('/api/models'), api('/api/voices'), api('/api/assets'),
      api('/api/generations'), api('/api/jobs'), api('/api/training'), api('/api/settings'),
      api('/api/system'), api('/api/runtime'),
    ]);
    Object.assign(state, {
      online: true, health, models: models.items, voices: voices.items, assets: assets.items,
      generations: generations.items, jobs: jobs.items, training: training.items,
      settings, system, runtime,
    });
    setLocalePreference(settings.interface_language || 'system', { translate: false });
    syncDefaultScript();
    state.selectedModel ||= settings.default_model_type || models.items[0]?.model_type;
    if (!state.models.some((model) => model.model_type === state.selectedModel)) state.selectedModel = state.models[0]?.model_type;
    state.editor.assetId ||= state.assets[0]?.id || null;
    state.selectedGenerationId ||= state.generations[0]?.id || null;
    updateChrome();
    await loadModelSchema(state.selectedModel, false);
  } catch (error) {
    state.online = false;
    state.models = state.models.length ? state.models : DEMO_MODELS;
    state.selectedModel ||= 'qwen3tts';
    state.schema ||= fallbackSchema(currentModel());
    updateChrome();
    if (!quiet) toast(`The local engine is offline: ${error.message}`, 'error');
  }
  render();
}

function fallbackSchema(model) {
  return {
    model: model || DEMO_MODELS[0],
    generation: [
      { name: 'seed', label: 'Seed', source: 'generation_config', control: 'number', default: null },
      { name: 'speed', label: 'Speed', source: 'generation_config', control: 'range', min: .25, max: 3, step: .05, default: 1 },
      { name: 'temperature', label: 'Temperature', source: 'generation_config', control: 'range', min: 0, max: 2, step: .01, default: .8 },
      { name: 'top_p', label: 'Top P', source: 'generation_config', control: 'range', min: 0, max: 1, step: .01, default: .95 },
      { name: 'max_new_tokens', label: 'Maximum new tokens', source: 'generation_config', control: 'number', default: null },
    ],
    conditioning: [
      { name: 'language', label: 'Language', source: 'model_kwargs', control: 'text', default: 'Auto', group: 'conditioning' },
      { name: 'speaker', label: 'Preset speaker', source: 'model_kwargs', control: 'text', default: '', group: 'conditioning' },
      { name: 'instruct', label: 'Delivery / voice instruction', source: 'model_kwargs', control: 'textarea', default: '', group: 'expression' },
    ],
    model_config: [], training: { support: 'unknown' }, advanced_json: true,
  };
}

async function loadModelSchema(modelType, rerender = true) {
  if (!modelType) return;
  state.selectedModel = modelType;
  state.schemaLoading = true;
  if (rerender) render();
  try {
    state.schema = state.online ? await api(`/api/models/${encodeURIComponent(modelType)}`) : fallbackSchema(currentModel());
  } catch (error) {
    state.schema = fallbackSchema(currentModel());
    toast(`Model controls could not be inspected: ${error.message}`, 'error');
  } finally {
    state.schemaLoading = false;
    if (rerender) render();
  }
}

function updateChrome() {
  const engine = $('#engine-card');
  if (engine) engine.innerHTML = state.online
    ? `<span class="status-dot"></span><div><strong>Engine ready</strong><small>VoiceHub ${escapeHtml(state.health?.voicehub_version || 'not installed')}</small></div>`
    : `<span class="status-dot offline"></span><div><strong>Engine offline</strong><small>Preview mode</small></div>`;
  const gpu = state.system?.accelerators?.[0];
  const compute = gpu
    ? `${gpu.name}${state.system?.torch?.cuda_available ? '' : ' · driver only'}`
    : state.online ? 'CPU' : 'Engine offline';
  const pill = $('#hardware-pill');
  if (pill) pill.innerHTML = `<span class="status-dot ${state.online ? '' : 'offline'}"></span><span>${escapeHtml(compute)}</span>`;
  const active = state.jobs.filter((job) => ['queued', 'running'].includes(job.status)).length;
  const count = $('#queue-count');
  if (count) { count.textContent = active; count.classList.toggle('hidden', !active); }
  const language = $('#language-toggle-label');
  if (language) language.textContent = getLocale() === 'tr' ? 'EN' : 'TR';
}

function pageHeading(eyebrow, title, description, actions = '') {
  return `<div class="page-heading"><div><div class="eyebrow">${escapeHtml(t(eyebrow))}</div><h1>${escapeHtml(t(title))}</h1><p>${escapeHtml(t(description))}</p></div>${actions ? `<div class="page-actions">${actions}</div>` : ''}</div>`;
}

function emptyState(iconName, title, copy, action = '') {
  return `<div class="empty-state"><span class="empty-icon">${icon(iconName)}</span><h3>${escapeHtml(t(title))}</h3><p>${escapeHtml(t(copy))}</p>${action}</div>`;
}

function statusBadge(status) {
  return `<span class="status-badge ${attr(status || 'queued')}">${escapeHtml(t(status || 'queued'))}</span>`;
}

function render() {
  const page = $('#page');
  if (!page) return;
  const renderer = {
    generate: renderGenerate, voices: renderVoices, editor: renderEditor,
    models: renderModels, training: renderTraining, queue: renderQueue, settings: renderSettings,
  }[state.route] || renderGenerate;
  page.innerHTML = renderer();
  $('#route-title').textContent = ROUTES[state.route][0];
  $$('.nav-item[data-route]').forEach((item) => item.classList.toggle('active', item.dataset.route === state.route));
  document.title = `${ROUTES[state.route][0]} · VoiceHub Studio`;
  hydrateIcons(page);
  updateChrome();
  localizeTree(document);
  if (state.route === 'editor') requestAnimationFrame(prepareWaveform);
}

function fieldInput(field, value, { idPrefix = 'setting', source = null } = {}) {
  const id = `${idPrefix}-${field.name}`;
  const data = `data-dynamic-field="true" data-field-name="${attr(field.name)}" data-field-source="${attr(source || field.source || 'model_kwargs')}"`;
  const common = `id="${id}" ${data} ${field.required ? 'required' : ''}`;
  const chosen = value ?? field.default ?? '';
  let input;
  const structured = Array.isArray(chosen) || (chosen && typeof chosen === 'object');
  if (field.control === 'switch' && field.default == null) {
    input = `<select class="select" ${common} data-nullable-boolean="true"><option value="">Model default</option><option value="true">Enabled</option><option value="false">Disabled</option></select>`;
  } else if (field.control === 'select' && field.choices?.length) {
    input = `<select class="select" ${common}>${field.choices.map((choice) => `<option value="${attr(choice)}" ${String(chosen) === String(choice) ? 'selected' : ''}>${escapeHtml(slugLabel(choice))}</option>`).join('')}</select>`;
  } else if (field.control === 'asset') {
    input = `<select class="select" ${common}><option value="">None</option>${state.assets.map((asset) => `<option value="asset:${attr(asset.id)}" ${String(chosen).replace('asset:', '') === asset.id ? 'selected' : ''}>${escapeHtml(asset.name)} · ${escapeHtml(formatDuration(asset.duration))}</option>`).join('')}</select>`;
  } else if (field.control === 'textarea' || structured) {
    const rendered = structured ? JSON.stringify(chosen, null, 2) : chosen;
    input = `<textarea class="textarea ${structured ? 'mono' : ''}" ${common} ${structured ? 'data-structured-value="true"' : ''} placeholder="${attr(field.help || `Enter ${field.label.toLowerCase()}`)}">${escapeHtml(rendered)}</textarea>`;
  } else if (field.control === 'switch') {
    input = `<label class="switch-row"><span><strong>${escapeHtml(field.label)}</strong><small>${escapeHtml(field.help || field.name)}</small></span><span class="switch"><input type="checkbox" ${common} ${chosen ? 'checked' : ''}><i></i></span></label>`;
    return input;
  } else if (field.control === 'range') {
    const min = field.min ?? 0; const max = field.max ?? 2; const step = field.step ?? .01;
    const optional = chosen === '';
    const rangeValue = optional ? (min + max) / 2 : chosen;
    input = `<div class="range-wrap"><input type="range" min="${attr(min)}" max="${attr(max)}" step="${attr(step)}" value="${attr(rangeValue)}" ${common} ${optional ? 'disabled' : ''}>${optional ? `<label class="range-value optional-range"><input type="checkbox" data-range-enable="${attr(id)}"><span>Auto</span></label>` : `<output class="range-value"><span>${escapeHtml(rangeValue)}</span></output>`}</div>`;
  } else if (field.control === 'text' && field.suggestions?.length) {
    const suggestionsId = `${id}-suggestions`;
    input = `<input class="input" type="text" value="${attr(chosen)}" list="${attr(suggestionsId)}" ${common} placeholder="${attr(field.help || (field.required ? 'Required' : 'Optional'))}"><datalist id="${attr(suggestionsId)}">${field.suggestions.map((suggestion) => `<option value="${attr(suggestion)}"></option>`).join('')}</datalist>`;
  } else {
    const number = field.control === 'number';
    input = `<input class="input" type="${number ? 'number' : 'text'}" value="${attr(chosen)}" ${number && field.min != null ? `min="${attr(field.min)}"` : ''} ${number && field.max != null ? `max="${attr(field.max)}"` : ''} ${number ? `step="${attr(field.step ?? 'any')}"` : ''} ${common} placeholder="${attr(field.help || (field.required ? 'Required' : 'Optional'))}">`;
  }
  return `<div class="field ${field.control === 'textarea' || structured ? 'full' : ''}"><label for="${id}">${escapeHtml(field.label)}${field.required ? '<small>required</small>' : ''}</label>${input}${field.help ? `<p class="field-help">${escapeHtml(field.help)}</p>` : ''}</div>`;
}

function preferredLanguage(field, model) {
  const configured = state.settings.default_language || field.default;
  if (String(configured).toLowerCase() === 'tr' && !model?.supports_turkish) return field.default;
  return configured;
}

function schemaField(name) {
  return [...(state.schema?.conditioning || []), ...(state.schema?.generation || []), ...(state.schema?.model_config || [])].find((field) => field.name === name);
}

function renderGenerate() {
  const model = currentModel();
  const schema = state.schema || fallbackSchema(model);
  const generation = currentGeneration();
  const activeVoiceOptions = state.voices.filter((voice) => !voice.model_type || voice.model_type === state.selectedModel);
  const visibleNames = new Set(['language', 'speaker', 'voice', 'instruct', 'instruction', 'description', 'emotion', 'speed', 'temperature', 'top_p']);
  let expressionFields = schema.conditioning.filter((field) => ['language', 'speaker', 'voice', 'instruct', 'instruction', 'description', 'emotion'].includes(field.name));
  if (state.generationMode === 'design') expressionFields = expressionFields.filter((field) => !['instruct', 'instruction', 'description'].includes(field.name));
  const sliderFields = schema.generation.filter((field) => ['speed', 'temperature', 'top_p'].includes(field.name));
  const advanced = [...schema.generation, ...schema.conditioning, ...schema.model_config].filter((field) => !visibleNames.has(field.name) && field.name !== 'mode');
  const checkpoint = state.checkpointOverride || (state.settings.default_model_type === state.selectedModel
    ? state.settings.default_checkpoint
    : model?.default_checkpoint);
  const device = state.settings.default_device || 'auto';
  const dtype = state.settings.default_dtype || 'auto';
  const availableModes = [
    ['synthesize', 'sparkles', 'Speak'],
    ...(model?.can_clone ? [['clone', 'clone', 'Clone']] : []),
    ...(model?.can_design ? [['design', 'wand', 'Design']] : []),
  ];
  const recent = state.generations.slice(0, 6);
  const checkpointChoices = CHECKPOINT_VARIANTS[state.selectedModel]?.choices || [];
  return `
    ${pageHeading('Voice synthesis', 'Make a voice say anything', 'Choose a VoiceHub model, shape its delivery, and render locally on CPU or GPU.', `<button class="button secondary" data-action="turkish-mode">${icon('sparkles')} Turkish setup</button><button class="button secondary" data-action="open-models">${icon('blocks')} Browse models</button>`)}
    ${!state.online ? `<div class="notice warning" style="margin-bottom:16px">${icon('warning')}<div><strong>Interface preview mode.</strong> Start the local service to load models and create audio.</div></div>` : ''}
    <div class="generate-layout">
      <form class="card composer-card" id="generation-form">
        <div class="composer-top">
          <div class="segmented" aria-label="Generation mode">
            ${availableModes.map(([mode, glyph, label]) => `<button type="button" class="${state.generationMode === mode ? 'active' : ''}" data-action="generation-mode" data-mode="${mode}">${icon(glyph)} ${label}</button>`).join('')}
          </div>
          <span class="badge ${state.online ? 'accent' : 'orange'}">${state.online ? `${state.models.length} models ready` : 'offline preview'}</span>
        </div>
        <div class="composer-content">
          <section class="composer-section">
            <h2 class="section-title">Engine <span>Model and checkpoint</span></h2>
            <div class="model-picker-grid">
              <div class="field"><label for="gen-model">VoiceHub model</label><select class="select" id="gen-model" name="model_type">${state.models.map((item) => `<option value="${attr(item.model_type)}" ${item.model_type === state.selectedModel ? 'selected' : ''}>${escapeHtml(item.display_name)}</option>`).join('')}</select></div>
              <div class="field"><label for="gen-checkpoint">Checkpoint <small>Hugging Face or local path</small></label><input class="input mono" id="gen-checkpoint" name="checkpoint" value="${attr(checkpoint || '')}" ${checkpointChoices.length ? 'list="checkpoint-suggestions"' : ''} required>${checkpointChoices.length ? `<datalist id="checkpoint-suggestions">${checkpointChoices.map((choice) => `<option value="${attr(choice)}"></option>`).join('')}</datalist>` : ''}${state.selectedModel === 'qwen3tts' ? `<p class="field-help">Qwen uses checkpoint-specific modes; switching Speak, Clone, or Design selects a compatible official variant.</p>` : ''}</div>
            </div>
            ${model?.supports_turkish ? `<div class="notice turkish-ready">${icon('check')}<span>Turkish is supported by this adapter. Use <strong>${escapeHtml(model.turkish?.language || model.turkish?.checkpoint || 'tr')}</strong>${model.turkish?.requires_reference ? ' with an authorized reference voice' : ''}.${model.turkish?.license ? ` <strong>License:</strong> ${escapeHtml(model.turkish.license)}.` : ''}</span></div>` : String(state.settings.default_language).toLowerCase() === 'tr' ? `<div class="notice warning">${icon('warning')}<span>This adapter does not advertise Turkish support. Use Turkish setup to select a compatible local model.</span></div>` : ''}
          </section>
          <section class="composer-section">
            <h2 class="section-title">Script <span>What should the voice say?</span></h2>
            <div class="script-wrap"><textarea class="textarea script-textarea" id="generation-text" name="text" maxlength="200000" required placeholder="Write or paste your script here…">${escapeHtml(state.generationText)}</textarea><div class="script-meta"><span id="script-words">${state.generationText.trim() ? state.generationText.trim().split(/\s+/).length : 0} words</span><span id="script-chars">${state.generationText.length.toLocaleString()} / 200,000</span></div></div>
          </section>
          <section class="composer-section">
            <h2 class="section-title">Voice & delivery <span>${escapeHtml(slugLabel(state.generationMode))}</span></h2>
            <div class="conditioning-panel">
              <div class="field full"><label for="gen-voice">Saved voice</label><select class="select" id="gen-voice" name="voice_id"><option value="">No saved profile</option>${activeVoiceOptions.map((voice) => `<option value="${attr(voice.id)}" ${voice.id === state.selectedVoiceId ? 'selected' : ''}>${escapeHtml(voice.name)} · ${escapeHtml(slugLabel(voice.kind))}</option>`).join('')}</select><p class="field-help">Voice profiles apply reference audio, design prompts, or preset speakers automatically.</p></div>
              ${state.generationMode === 'clone' ? renderDirectCloneFields(schema) : ''}
              ${state.generationMode === 'design' ? renderDirectDesignFields(schema) : ''}
              ${expressionFields.map((field) => fieldInput(field, state.selectedVoiceId ? '' : field.name === 'language' ? preferredLanguage(field, model) : field.default)).join('')}
            </div>
          </section>
          ${sliderFields.length ? `<section class="composer-section"><h2 class="section-title">Sampling <span>Model-aware generation controls</span></h2><div class="generation-sliders">${sliderFields.map((field) => fieldInput(field, field.default)).join('')}</div></section>` : ''}
          <details class="advanced-disclosure">
            <summary>${icon('sliders')} Every model setting <span class="summary-hint">${advanced.length} discovered · JSON overrides included</span></summary>
            <div class="advanced-content">
              <div class="advanced-field-grid">${advanced.map((field) => fieldInput(field, field.default)).join('')}</div>
              <h3 class="section-title" style="margin-top:18px">Per-render output & compute</h3>
              <div class="advanced-field-grid">
                <div class="field"><label for="gen-device">Device</label>${deviceSelect('gen-device', 'device', device)}</div>
                <div class="field"><label for="gen-dtype">Precision</label><select class="select" id="gen-dtype">${['auto', 'float32', 'float16', 'bfloat16'].map((value) => `<option ${dtype === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div>
                <div class="field"><label for="gen-format">Format</label><select class="select" id="gen-format">${['wav', 'flac', 'mp3', 'ogg'].map((value) => `<option ${state.settings.output_format === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div>
                <div class="field"><label for="gen-rate">Sample rate <small>blank keeps native</small></label><input class="input" id="gen-rate" type="number" min="8000" max="192000" value="${attr(state.settings.output_sample_rate ?? '')}" placeholder="Native"></div>
                <div class="field"><label for="gen-channels">Channels</label><select class="select" id="gen-channels"><option value="1" ${state.settings.output_channels === 1 ? 'selected' : ''}>Mono</option><option value="2" ${state.settings.output_channels === 2 ? 'selected' : ''}>Stereo</option></select></div>
                <label class="switch-row"><span><strong>Normalize output</strong><small>EBU R128 loudness pass</small></span><span class="switch"><input id="gen-normalize" type="checkbox"><i></i></span></label>
              </div>
              <div class="form-grid" style="margin-top:14px">
                <div class="field full"><label for="advanced-model-json">Model keyword overrides <small>JSON</small></label><textarea class="textarea mono" id="advanced-model-json" placeholder='{"exaggeration": 0.5}'>{}</textarea></div>
                <div class="field full"><label for="advanced-config-json">Model loading overrides <small>JSON</small></label><textarea class="textarea mono" id="advanced-config-json" placeholder='{"low_cpu_mem_usage": true}'>{}</textarea></div>
                <div class="field full"><label for="advanced-generation-json">Generation overrides <small>JSON</small></label><textarea class="textarea mono" id="advanced-generation-json" placeholder='{"do_sample": true}'>{}</textarea></div>
              </div>
            </div>
          </details>
        </div>
        <div class="composer-footer">
          <div class="output-summary"><strong>${escapeHtml((state.settings.output_format || 'wav').toUpperCase())} · ${state.settings.output_sample_rate ? `${Number(state.settings.output_sample_rate).toLocaleString()} Hz` : 'native rate'} · ${state.settings.output_channels === 2 ? 'stereo' : 'mono'}</strong><small>${escapeHtml(device)} · ${escapeHtml(dtype)} · jobs run safely in the background</small></div>
          <button class="button large" type="submit" ${!state.online || state.schemaLoading ? 'disabled' : ''}>${icon('sparkles')} Generate speech</button>
        </div>
      </form>
      <aside class="preview-column">
        <div class="card preview-card"><div class="card-header"><div><h2>Latest output</h2><p>Audio appears here as soon as the job finishes</p></div>${generation ? `<div class="header-actions">${statusBadge(generation.status)}</div>` : ''}</div><div class="preview-stage">${renderOutputPreview(generation)}</div></div>
        <div class="card"><div class="card-header"><div><h2>Recent generations</h2><p>Reopen or download previous results</p></div>${recent.length ? `<div class="header-actions"><button class="button ghost small" data-action="go-queue">View queue</button></div>` : ''}</div>${recent.length ? `<div class="history-list">${recent.map(renderHistoryRow).join('')}</div>` : emptyState('waveform', 'Nothing rendered yet', 'Your recent generations will stay here for quick comparison.')}</div>
      </aside>
    </div>`;
}

function renderDirectCloneFields(schema) {
  const audioField = schema.conditioning.find((field) => field.control === 'asset') || { name: 'speaker_audio_path', label: 'Reference audio', source: 'model_kwargs', control: 'asset', required: true };
  const textField = schema.conditioning.find((field) => ['reference_text', 'prompt_text'].includes(field.name));
  return `${fieldInput(audioField, '')}${textField ? fieldInput(textField, '') : ''}`;
}

function renderDirectDesignFields(schema) {
  const field = schema.conditioning.find((item) => ['instruct', 'instruction', 'description', 'prompt'].includes(item.name)) || { name: 'instruct', label: 'Voice design prompt', source: 'model_kwargs', control: 'textarea', required: true };
  return fieldInput({ ...field, label: 'Voice design prompt' }, state.selectedVoiceId ? '' : 'A warm, confident voice with natural pacing and subtle enthusiasm.');
}

function renderOutputPreview(generation) {
  if (!generation) return `<div class="preview-empty"><div class="preview-orb">${icon('waveform')}</div><h3>Your next take starts here</h3><p>Configure a model and voice, then generate. Nothing leaves this computer.</p></div>`;
  const processing = ['queued', 'running'].includes(generation.status);
  const bars = Array.from({ length: 42 }, (_, index) => `<i style="height:${14 + ((index * 17 + 11) % 55)}px"></i>`).join('');
  return `<div class="active-output">
    <div class="output-topline"><span class="badge ${processing ? 'cyan' : generation.status === 'failed' ? 'orange' : 'accent'}">${processing ? 'Processing locally' : escapeHtml(generation.status)}</span><span class="badge">${escapeHtml(generation.output_format?.toUpperCase() || 'WAV')}</span></div>
    <h3 class="output-title">${escapeHtml(truncate(generation.text, 58))}</h3>
    <div class="output-subtitle">${escapeHtml(generation.model_type)} · ${escapeHtml(generation.device || 'auto')} · ${formatDate(generation.created_at)}</div>
    <div class="mini-waveform ${processing ? 'processing' : ''}">${bars}</div>
    ${generation.audio_url ? `<audio class="audio-player" controls preload="metadata" src="${attr(generation.audio_url)}"></audio>` : generation.error ? `<div class="notice danger">${icon('warning')}<span>${escapeHtml(truncate(generation.error, 240))}</span></div>` : `<div class="notice">${icon('clock')}<span>${processing ? 'The model job is running in the background. You can move around the studio.' : 'No output file is available.'}</span></div>`}
    <div class="output-metrics"><div class="metric"><strong>${escapeHtml(formatDuration(generation.duration))}</strong><small>Duration</small></div><div class="metric"><strong>${generation.latency ? `${Number(generation.latency).toFixed(2)} s` : '—'}</strong><small>Render time</small></div><div class="metric"><strong>${generation.sample_rate ? Number(generation.sample_rate).toLocaleString() : 'Native'}</strong><small>Sample rate</small></div></div>
  </div>`;
}

function renderHistoryRow(generation) {
  return `<div class="history-row"><button class="history-play" data-action="select-generation" data-id="${attr(generation.id)}" aria-label="Open generation">${generation.status === 'completed' ? icon('play') : icon('clock')}</button><div class="history-copy"><strong>${escapeHtml(truncate(generation.text, 54))}</strong><small>${escapeHtml(generation.model_type)} · ${formatDate(generation.created_at)}</small></div>${statusBadge(generation.status)}</div>`;
}

function renderVoices() {
  const query = state.voiceSearch.toLowerCase();
  const voices = state.voices.filter((voice) => {
    const matchesText = !query || [voice.name, voice.kind, voice.model_type, ...(voice.tags || [])].join(' ').toLowerCase().includes(query);
    return matchesText && (state.voiceFilter === 'all' || voice.kind === state.voiceFilter || (state.voiceFilter === 'favorite' && voice.favorite));
  });
  const kinds = { clone: 0, design: 0, preset: 0, recording: 0 };
  state.voices.forEach((voice) => { if (voice.kind in kinds) kinds[voice.kind] += 1; });
  return `
    ${pageHeading('Voice library', 'Build a cast you can reuse', 'Import an authorized voice, record a reference, describe a new voice, or save a model preset.', `<button class="button" data-action="new-voice">${icon('plus')} Add voice</button>`)}
    <div class="voice-stats">
      ${renderStat('voices', state.voices.length, 'All voices', 'accent')}
      ${renderStat('clone', kinds.clone + kinds.recording, 'Reference voices', 'cyan')}
      ${renderStat('wand', kinds.design, 'Designed voices', 'violet')}
      ${renderStat('star', state.voices.filter((voice) => voice.favorite).length, 'Favorites', 'orange')}
    </div>
    <div class="toolbar card" style="margin-bottom:14px">
      <div class="input-group"><span data-icon="search"></span><input class="input" id="voice-search" value="${attr(state.voiceSearch)}" placeholder="Search voices, tags, or models"></div>
      <div class="filter-tabs">${['all', 'clone', 'design', 'preset', 'favorite'].map((kind) => `<button class="filter-tab ${state.voiceFilter === kind ? 'active' : ''}" data-action="voice-filter" data-filter="${kind}">${escapeHtml(slugLabel(kind))}</button>`).join('')}</div>
    </div>
    <div class="voice-grid">
      <button class="card add-voice-card" data-action="new-voice"><span class="empty-icon">${icon('plus')}</span><strong>Add a voice</strong><small>Clone, record, design, or save a preset</small></button>
      ${voices.map(renderVoiceCard).join('')}
    </div>
    ${!voices.length && state.voices.length ? emptyState('search', 'No matching voices', 'Change the search or filter to see more voice profiles.') : ''}`;
}

function renderStat(glyph, number, title, tone) {
  return `<div class="stat-card"><span class="stat-icon ${tone}">${icon(glyph)}</span><div class="stat-copy"><strong>${escapeHtml(number)}</strong><small>${escapeHtml(title)}</small></div></div>`;
}

function voiceDescription(voice) {
  if (voice.kind === 'design') return voice.design_prompt || 'Designed from a natural-language voice prompt.';
  if (voice.kind === 'preset') return `Preset speaker: ${voice.speaker || 'model default'}`;
  if (voice.reference_text) return `Reference: “${truncate(voice.reference_text, 100)}”`;
  return 'Authorized reference audio voice profile.';
}

function renderVoiceCard(voice) {
  return `<article class="card voice-card">
    <div class="voice-card-top"><span class="voice-avatar ${attr(voice.kind)}">${escapeHtml(initials(voice.name))}</span><div class="voice-card-title"><h3>${escapeHtml(voice.name)}</h3><p>${escapeHtml(slugLabel(voice.kind))} · ${escapeHtml(voice.model_type || 'any compatible model')}</p></div><button class="favorite-button ${voice.favorite ? 'active' : ''}" data-action="favorite-voice" data-id="${attr(voice.id)}" aria-label="Toggle favorite">${icon('star')}</button></div>
    <div class="voice-card-body"><p class="voice-description">${escapeHtml(voiceDescription(voice))}</p><div class="chip-row">${(voice.tags || []).slice(0, 4).map((tag) => `<span class="capability-chip">${escapeHtml(tag)}</span>`).join('')}${voice.language ? `<span class="capability-chip">${escapeHtml(voice.language)}</span>` : ''}</div></div>
    <div class="voice-card-footer"><small>${escapeHtml(voice.checkpoint || 'Uses current checkpoint')}</small>${voice.reference_audio_url ? `<button class="button ghost small" data-action="preview-voice" data-url="${attr(voice.reference_audio_url)}">${icon('play')}</button>` : ''}<button class="button secondary small" data-action="use-voice" data-id="${attr(voice.id)}">Use</button><button class="button ghost small" data-action="edit-voice" data-id="${attr(voice.id)}">${icon('edit')}</button></div>
  </article>`;
}

function renderEditor() {
  const asset = currentAsset();
  const operations = state.editor.operations;
  return `
    ${pageHeading('Audio workshop', 'Cut clean, keep the character', 'Every edit creates a new asset, so the original recording is always preserved.', `<button class="button secondary" data-action="concat-assets">${icon('layers')} Combine</button><button class="button" data-action="upload-audio">${icon('upload')} Import audio</button>`)}
    <div class="editor-layout">
      <aside class="card asset-browser">
        <div class="card-header"><div><h2>Audio assets</h2><p>${state.assets.length} files in the local library</p></div><div class="header-actions"><button class="button ghost small" data-action="upload-audio">${icon('plus')}</button></div></div>
        ${state.assets.length ? `<div class="asset-list">${state.assets.map((item) => `<button class="asset-row ${item.id === state.editor.assetId ? 'active' : ''}" data-action="select-asset" data-id="${attr(item.id)}"><span class="asset-kind">${icon(item.kind === 'generation' ? 'sparkles' : 'waveform')}</span><span class="asset-copy"><strong>${escapeHtml(item.name)}</strong><small>${formatDuration(item.duration)} · ${item.sample_rate ? `${Number(item.sample_rate).toLocaleString()} Hz` : 'audio'}</small></span></button>`).join('')}</div>` : emptyState('upload', 'No audio yet', 'Import WAV, FLAC, MP3, OGG, M4A, or another FFmpeg-readable file.', `<button class="button small" data-action="upload-audio">Import audio</button>`)}
      </aside>
      <div class="editor-workspace">
        ${asset ? renderWaveformCard(asset) : `<div class="card">${emptyState('waveform', 'Choose an audio source', 'Import a recording or select a generated take to start editing.', `<button class="button" data-action="upload-audio">${icon('upload')} Import audio</button>`)}</div>`}
        ${asset ? `<div class="effects-layout">
          <section class="card"><div class="card-header"><div><h2>Processing rack</h2><p>Add effects in the order they should be rendered</p></div></div><div class="effects-grid">
            ${renderEffect('normalize', 'activity', 'Normalize', 'Target loudness')}
            ${renderEffect('denoise', 'magic', 'Denoise', 'Reduce steady noise')}
            ${renderEffect('gain', 'volume', 'Gain', 'Raise or lower level')}
            ${renderEffect('speed', 'redo', 'Speed', 'Change tempo')}
            ${renderEffect('pitch', 'waveform', 'Pitch', 'Shift semitones')}
            ${renderEffect('fade_in', 'activity', 'Fade in', 'Smooth beginning')}
            ${renderEffect('fade_out', 'activity', 'Fade out', 'Smooth ending')}
            ${renderEffect('trim_silence', 'scissors', 'Trim silence', 'Clean both ends')}
            ${renderEffect('compress', 'sliders', 'Compress', 'Control dynamics')}
            ${renderEffect('reverse', 'redo', 'Reverse', 'Flip in time')}
            ${renderEffect('highpass', 'filter', 'High-pass', 'Remove rumble')}
            ${renderEffect('lowpass', 'filter', 'Low-pass', 'Soften highs')}
          </div></section>
          <aside class="card"><div class="card-header"><div><h2>Operation stack</h2><p>${operations.length} queued edits</p></div><div class="header-actions">${operations.length ? `<button class="button ghost small" data-action="clear-operations">Clear</button>` : ''}</div></div>
            <div class="operation-stack">${operations.length ? operations.map(renderOperation).join('') : `<div class="empty-state" style="min-height:205px;padding:18px"><span class="empty-icon">${icon('layers')}</span><h3>No edits queued</h3><p>Select a range or add an effect.</p></div>`}</div>
            <div class="form-footer"><small>Original stays untouched</small><button class="button" data-action="apply-edits" ${!operations.length || !state.online ? 'disabled' : ''}>${icon('sparkles')} Render edit</button></div>
          </aside>
        </div>` : ''}
      </div>
    </div>`;
}

function renderWaveformCard(asset) {
  return `<section class="card waveform-card">
    <div class="transport"><button class="icon-button" data-action="play-asset">${icon('play')}</button><button class="icon-button" data-action="stop-asset">${icon('stop')}</button><span class="transport-time" id="transport-time">0:00.00 / ${formatDuration(asset.duration)}</span><strong class="asset-name">${escapeHtml(asset.name)}</strong><span class="transport-meta">${asset.channels || '?'} ch · ${asset.sample_rate ? Number(asset.sample_rate).toLocaleString() : '?'} Hz</span><button class="icon-button" data-action="delete-asset" data-id="${attr(asset.id)}" title="Delete asset">${icon('trash')}</button><audio id="editor-audio" preload="metadata" src="${attr(asset.content_url)}"></audio></div>
    <div class="waveform-stage" id="waveform-stage"><canvas id="waveform-canvas"></canvas></div>
    <div class="selection-readout"><div class="selection-values"><span>IN <strong id="selection-start">${formatDuration(state.editor.start)}</strong></span><span>OUT <strong id="selection-end">${formatDuration(state.editor.end || asset.duration)}</strong></span><span>LENGTH <strong id="selection-length">${formatDuration((state.editor.end || asset.duration) - state.editor.start)}</strong></span></div><div class="selection-actions"><button class="button ghost small" data-action="auto-segments">${icon('magic')} Auto-cut speech</button><button class="button secondary small" data-action="preview-selection">${icon('play')} Preview</button><button class="button secondary small" data-action="keep-selection">Keep</button><button class="button danger small" data-action="delete-selection">Delete</button></div></div>
  </section>`;
}

function renderEffect(op, glyph, title, copy) {
  return `<button class="effect-tile" data-action="add-effect" data-effect="${attr(op)}"><span>${icon(glyph)}</span><div><strong>${escapeHtml(title)}</strong><small>${escapeHtml(copy)}</small></div></button>`;
}

function operationSummary(operation) {
  const values = Object.entries(operation).filter(([key]) => key !== 'op').map(([key, value]) => `${slugLabel(key)}: ${Array.isArray(value) ? `${value.length} ranges` : value}`).join(' · ');
  return values || 'Default parameters';
}

function renderOperation(operation, index) {
  return `<div class="operation-row"><span class="operation-index">${index + 1}</span><div><strong>${escapeHtml(slugLabel(operation.op))}</strong><small>${escapeHtml(operationSummary(operation))}</small></div><button class="operation-remove" data-action="remove-operation" data-index="${index}" aria-label="Remove operation">${icon('x')}</button></div>`;
}

const MODEL_DESCRIPTIONS = {
  qwen3tts: 'One family for preset voices, natural-language voice design, and high-fidelity cloning.',
  chatterbox: 'Expressive zero-shot voice cloning with exaggeration and classifier-free guidance controls.',
  f5tts: 'Flow-matching speech synthesis with reference-audio cloning and multilingual support.',
  kokoro: 'Compact, fast synthesis with a broad collection of high-quality preset voices.',
  xtts: 'Multilingual zero-shot cloning designed for cross-language speaker transfer.',
  dia: 'Natural dialogue generation with multiple speakers and conversational delivery.',
  cosyvoice: 'Multilingual speech, cross-lingual cloning, and instruction-driven style control.',
  parlertts: 'Describe the speaker and delivery in natural language to design a new performance.',
  zonos: 'Expressive synthesis and cloning with detailed emotion and conditioning controls.',
  zonos2: 'Second-generation expressive synthesis with flexible speaker and emotion conditioning.',
  omnivoice: 'Voice cloning and voice design through a unified prompt-oriented model.',
  voxcpm: 'Context-aware speech generation with cloning and natural-language voice design.',
  openvoice: 'Instant cloning with flexible tone-color transfer across languages and accents.',
  gptsovits: 'Few-shot multilingual voice cloning with semantic and acoustic modeling.',
  bark: 'Generative audio capable of expressive speech, non-verbal sounds, and multiple languages.',
  vits: 'Classic end-to-end neural TTS, including MMS checkpoints for wide language coverage.',
};

function renderModels() {
  const needle = state.modelSearch.toLowerCase();
  const filtered = state.models.filter((model) => {
    const matchesSearch = !needle || [model.display_name, model.model_type, model.default_checkpoint, ...(model.capabilities || [])].join(' ').toLowerCase().includes(needle);
    const matchesFilter = state.modelFilter === 'all'
      || (state.modelFilter === 'clone' && model.can_clone)
      || (state.modelFilter === 'design' && model.can_design)
      || (state.modelFilter === 'expressive' && model.can_style)
      || (state.modelFilter === 'train' && model.can_train)
      || (state.modelFilter === 'multilingual' && model.capabilities?.some((cap) => cap.includes('multilingual')))
      || (state.modelFilter === 'turkish' && model.supports_turkish);
    return matchesSearch && matchesFilter;
  });
  return `
    ${pageHeading('VoiceHub registry', `${state.models.length} models, one studio`, 'Adapters are discovered from the installed VoiceHub registry. No checkpoint is loaded until you ask for it.', `<button class="button secondary" data-action="refresh-workspace">${icon('refresh')} Refresh registry</button>`)}
    <div class="toolbar card" style="margin-bottom:14px"><div class="input-group"><span data-icon="search"></span><input class="input" id="model-search" value="${attr(state.modelSearch)}" placeholder="Search model, capability, or checkpoint"></div><div class="filter-tabs">${[['all', 'All'], ['clone', 'Cloning'], ['design', 'Design'], ['expressive', 'Expressive'], ['multilingual', 'Multilingual'], ['turkish', 'Turkish'], ['train', 'Fine-tunable']].map(([value, label]) => `<button class="filter-tab ${state.modelFilter === value ? 'active' : ''}" data-action="model-filter" data-filter="${value}">${label}</button>`).join('')}</div></div>
    <div class="model-grid">${filtered.map(renderModelCard).join('')}</div>
    ${!filtered.length ? emptyState('search', 'No matching models', 'Try a different capability filter or search term.') : ''}`;
}

function renderModelCard(model) {
  const loaded = state.runtime?.models?.some((item) => item.model_type === model.model_type);
  const turkishAction = state.modelFilter === 'turkish' && model.supports_turkish;
  return `<article class="card model-card">
    <div class="model-card-top"><span class="model-logo">${escapeHtml(model.display_name.slice(0, 2).toUpperCase())}</span><div class="model-title"><h3>${escapeHtml(model.display_name)}</h3><p>${escapeHtml(model.default_checkpoint)}</p></div>${loaded ? '<span class="status-badge ready">loaded</span>' : ''}</div>
    <div class="model-card-body"><p class="model-description">${escapeHtml(t(MODEL_DESCRIPTIONS[model.model_type] || `VoiceHub adapter for ${model.architecture || model.display_name}.`))}</p><div class="chip-row">${model.supports_turkish ? '<span class="capability-chip turkish-chip">Türkçe</span>' : ''}${(model.capabilities || []).slice(0, 4).map((capability) => `<span class="capability-chip">${escapeHtml(slugLabel(capability))}</span>`).join('')}</div><div class="model-meta"><div><small>Architecture</small><strong>${escapeHtml(model.architecture || 'Adapter')}</strong></div><div><small>Install extra</small><strong>${escapeHtml(model.install_extra || 'core')}</strong></div></div></div>
    <div class="model-card-footer"><button class="button ghost small" data-action="model-details" data-model="${attr(model.model_type)}">Details</button><button class="button secondary small" data-action="load-model" data-model="${attr(model.model_type)}">${icon('download')} Load</button><button class="button small" data-action="${turkishAction ? 'use-turkish-model' : 'use-model'}" data-model="${attr(model.model_type)}">${turkishAction ? 'Türkçe kullan' : 'Use'}</button></div>
  </article>`;
}

function renderTraining() {
  const model = currentModel();
  const trainingSchema = state.schema?.training || {};
  return `
    ${pageHeading('Model workshop', 'Fine-tune with a reproducible recipe', 'VoiceHub owns the training adapter and dataset contract; Studio manages configuration, progress, and artifacts.')}
    <div class="split-layout">
      <form class="card training-form" id="training-form">
        <div class="card-header"><div><h2>New training run</h2><p>Start small with a smoke test, then scale deliberately</p></div>${trainingSchema.support ? `<span class="badge ${trainingSchema.support === 'supported' ? 'accent' : 'orange'}">${escapeHtml(trainingSchema.support)}</span>` : ''}</div>
        <div class="card-body">
          <div class="form-section"><h3>Run identity</h3><div class="form-grid"><div class="field"><label for="train-name">Run name</label><input class="input" id="train-name" name="name" value="My voice fine-tune" required></div><div class="field"><label for="train-device">Compute device</label>${deviceSelect('train-device', 'device', state.settings.default_device || 'auto')}</div></div></div>
          <div class="form-section"><h3>Base model</h3><div class="form-grid"><div class="field"><label for="train-model">VoiceHub model</label><select class="select" id="train-model" name="model_type">${state.models.map((item) => `<option value="${attr(item.model_type)}" ${item.model_type === state.selectedModel ? 'selected' : ''}>${escapeHtml(item.display_name)}</option>`).join('')}</select></div><div class="field"><label for="train-checkpoint">Checkpoint</label><input class="input mono" id="train-checkpoint" name="checkpoint" value="${attr(trainingSchema.training_checkpoint || model?.default_checkpoint || '')}" required></div></div>${trainingSchema.error ? `<div class="notice warning" style="margin-top:12px">${icon('warning')}<span>${escapeHtml(trainingSchema.error)}</span></div>` : ''}</div>
          <div class="form-section"><h3>Dataset manifests</h3><div class="form-grid"><div class="field full"><label for="train-manifest">Training manifest <small>local JSONL / CSV path</small></label><input class="input mono" id="train-manifest" name="train_manifest" placeholder="/data/voice/train.jsonl" required><p class="field-help">The exact record schema is validated by the selected VoiceHub model family.</p></div><div class="field full"><label for="eval-manifest">Evaluation manifest <small>optional</small></label><input class="input mono" id="eval-manifest" name="eval_manifest" placeholder="/data/voice/eval.jsonl"></div></div></div>
          <div class="form-section"><h3>Recipe</h3><div class="form-grid three"><div class="field"><label for="train-steps">Maximum steps</label><input class="input" type="number" id="train-steps" min="1" value="1"></div><div class="field"><label for="train-batch">Batch size</label><input class="input" type="number" id="train-batch" min="1" value="1"></div><div class="field"><label for="train-lr">Learning rate</label><input class="input" type="number" id="train-lr" min="0" step="0.000001" value="0.00005"></div><div class="field"><label for="train-grad-accum">Gradient accumulation</label><input class="input" type="number" id="train-grad-accum" min="1" value="1"></div><div class="field"><label for="train-save-steps">Save every</label><input class="input" type="number" id="train-save-steps" min="1" value="100"></div><div class="field"><label for="train-log-steps">Log every</label><input class="input" type="number" id="train-log-steps" min="1" value="1"></div><div class="field full"><label for="train-config-json">Complete TrainingArguments overrides <small>JSON</small></label><textarea class="textarea mono" id="train-config-json">{}</textarea></div></div></div>
          <div class="notice warning">${icon('warning')}<div><strong>Fine-tuning is model-specific and compute intensive.</strong> A one-step smoke test is the default so dataset and adapter errors surface before a long run.</div></div>
        </div>
        <div class="form-footer"><small>Inference models are unloaded before training to free VRAM.</small><button class="button" type="submit" ${!state.online ? 'disabled' : ''}>${icon('sliders')} Start training</button></div>
      </form>
      <aside><div class="card" style="margin-bottom:14px"><div class="card-header"><div><h2>Adapter contract</h2><p>Reported by VoiceHub for the selected model</p></div></div><div class="card-body"><div class="form-grid"><div class="metric"><strong>${escapeHtml(trainingSchema.family || 'Unknown')}</strong><small>Family</small></div><div class="metric"><strong>${escapeHtml(trainingSchema.dataset_readiness || 'Unknown')}</strong><small>Dataset adapter</small></div><div class="metric"><strong>${trainingSchema.sample_rate ? Number(trainingSchema.sample_rate).toLocaleString() : 'Model default'}</strong><small>Sample rate</small></div><div class="metric"><strong>${escapeHtml(trainingSchema.support || 'Unknown')}</strong><small>Support</small></div></div></div></div><div class="run-list">${state.training.length ? state.training.slice(0, 8).map(renderTrainingRun).join('') : `<div class="card">${emptyState('sliders', 'No training runs', 'Completed and active fine-tunes will appear here.')}</div>`}</div></aside>
    </div>`;
}

function renderTrainingRun(run) {
  return `<article class="card run-card"><div class="run-top"><span class="job-kind-icon training">${icon('sliders')}</span><div class="run-title"><strong>${escapeHtml(run.name)}</strong><small>${escapeHtml(run.model_type)} · ${formatDate(run.created_at)}</small></div>${statusBadge(run.status)}</div><div class="progress-track"><i style="width:${clamp(Number(run.progress || 0) * 100, 0, 100)}%"></i></div><div class="run-bottom"><span>Step ${escapeHtml(run.current_step || 0)} / ${escapeHtml(run.total_steps || '?')}</span><span>${run.training_loss != null ? `loss ${Number(run.training_loss).toFixed(4)}` : run.output_dir}</span></div>${run.error ? `<pre class="job-error">${escapeHtml(run.error)}</pre>` : ''}</article>`;
}

function renderQueue() {
  const jobs = state.jobs.filter((job) => state.queueFilter === 'all' || job.status === state.queueFilter);
  const active = state.jobs.filter((job) => ['queued', 'running'].includes(job.status)).length;
  return `
    ${pageHeading('Local jobs', active ? `${active} job${active === 1 ? '' : 's'} in motion` : 'Everything is caught up', 'Long model loads, inference, editing, and fine-tuning continue safely while you use the studio.', `<button class="button secondary" data-action="refresh-workspace">${icon('refresh')} Refresh</button>`)}
    <div class="queue-toolbar"><div class="segmented">${['all', 'queued', 'running', 'completed', 'failed', 'cancelled'].map((filter) => `<button class="${state.queueFilter === filter ? 'active' : ''}" data-action="queue-filter" data-filter="${filter}">${escapeHtml(slugLabel(filter))}</button>`).join('')}</div><span class="badge">${state.jobs.length} retained</span></div>
    <div class="job-list">${jobs.length ? jobs.map(renderJob).join('') : `<div class="card">${emptyState('queue', 'No jobs in this view', 'New generation, editing, model loading, and training jobs will appear automatically.')}</div>`}</div>`;
}

function jobTitle(job) {
  const payload = job.payload || {};
  if (job.kind === 'tts.generate') return `Generate ${payload.generation_id || 'speech'}`;
  if (job.kind === 'model.load') return `Load ${payload.model_type || 'model'}`;
  if (job.kind === 'audio.edit') return payload.name || 'Render audio edit';
  if (job.kind === 'audio.concat') return payload.name || 'Combine audio';
  if (job.kind === 'model.train') return `Train ${payload.training_id || 'model'}`;
  return slugLabel(job.kind);
}

function renderJob(job) {
  const jobGroup = job.kind.startsWith('audio') ? 'audio' : job.kind === 'model.train' ? 'training' : '';
  const glyph = job.kind.startsWith('audio') ? 'waveform' : job.kind === 'model.train' ? 'sliders' : job.kind === 'model.load' ? 'download' : 'sparkles';
  return `<article class="card job-card"><div class="job-top"><span class="job-kind-icon ${jobGroup}">${icon(glyph)}</span><div class="job-title"><strong>${escapeHtml(jobTitle(job))}</strong><small>${escapeHtml(job.kind)} · ${formatDate(job.created_at)}</small></div>${statusBadge(job.status)}</div><div class="progress-track"><i style="width:${clamp(Number(job.progress || 0) * 100, 0, 100)}%"></i></div><div class="job-bottom"><span>${Math.round(Number(job.progress || 0) * 100)}%</span><span>${escapeHtml(job.stage || 'Waiting')}</span><span>${job.started_at ? `started ${formatDate(job.started_at)}` : 'queued locally'}</span>${['queued', 'running'].includes(job.status) ? `<button class="button danger small" data-action="cancel-job" data-id="${attr(job.id)}">Cancel</button>` : ''}</div>${job.error ? `<pre class="job-error">${escapeHtml(job.error)}</pre>` : ''}</article>`;
}

function deviceSelect(id, name, selected) {
  const devices = [{ id: 'auto', label: 'Auto-select', available: true }, ...(state.system?.devices || [{ id: 'cpu', label: 'CPU', available: true }])];
  return `<select class="select" id="${attr(id)}" name="${attr(name)}">${devices.map((device) => `<option value="${attr(device.id)}" ${device.id === selected ? 'selected' : ''} ${device.available === false ? 'disabled' : ''}>${escapeHtml(device.label)}${device.available === false ? ' (runtime unavailable)' : ''}</option>`).join('')}</select>`;
}

function renderSettings() {
  const settings = state.settings;
  const system = state.system || {};
  const gpu = system.accelerators?.[0];
  const disk = system.disk || {};
  const tabContent = {
    compute: renderComputeSettings,
    output: renderOutputSettings,
    runtime: renderRuntimeSettings,
    storage: renderStorageSettings,
    interface: renderInterfaceSettings,
  }[state.settingsTab] || renderComputeSettings;
  return `
    ${pageHeading('Studio preferences', 'Tune the machine around your workflow', 'Defaults can be overridden on every generation; nothing here locks you into one model or device.')}
    <div class="hardware-grid">
      <div class="card hardware-card"><span class="stat-icon cyan">${icon('gpu')}</span><div class="hardware-copy"><small>Accelerator</small><strong>${escapeHtml(gpu?.name || 'No GPU runtime')}</strong><span>${gpu ? `${Number(gpu.memory_free_mb || 0).toLocaleString()} / ${Number(gpu.memory_total_mb || 0).toLocaleString()} MB free` : 'CPU mode is always available'}</span></div></div>
      <div class="card hardware-card"><span class="stat-icon violet">${icon('cpu')}</span><div class="hardware-copy"><small>Processor</small><strong>${escapeHtml(system.platform?.cpu || 'Unknown CPU')}</strong><span>${escapeHtml(system.platform?.cpu_threads || '?')} threads · ${formatBytes(system.platform?.memory_total_bytes)} RAM</span></div></div>
      <div class="card hardware-card"><span class="stat-icon orange">${icon('database')}</span><div class="hardware-copy"><small>Local storage</small><strong>${formatBytes(disk.free_bytes)} free</strong><span>${escapeHtml(disk.path || 'Studio data directory')}</span></div></div>
    </div>
    <div class="settings-layout">
      <nav class="card settings-tabs">${[['compute', 'gpu', 'Compute'], ['output', 'waveform', 'Audio output'], ['runtime', 'activity', 'Runtime'], ['storage', 'folder', 'Storage'], ['interface', 'settings', 'Interface']].map(([tab, glyph, label]) => `<button class="settings-tab ${state.settingsTab === tab ? 'active' : ''}" data-action="settings-tab" data-tab="${tab}">${icon(glyph)} ${label}</button>`).join('')}</nav>
      <form class="card settings-form" id="settings-form">${tabContent(settings, system)}<div class="form-footer"><small>Saved to your XDG config directory.</small><button class="button" type="submit" ${!state.online ? 'disabled' : ''}>${icon('save')} Save settings</button></div></form>
    </div>`;
}

function settingsHeader(title, copy) { return `<div class="card-header"><div><h2>${escapeHtml(title)}</h2><p>${escapeHtml(copy)}</p></div></div>`; }

function renderComputeSettings(settings) {
  return `${settingsHeader('Compute defaults', 'Device, precision, and kernel preferences')}<div class="card-body"><div class="form-section"><div class="form-grid"><div class="field"><label for="setting-device">Default device</label>${deviceSelect('setting-device', 'default_device', settings.default_device || 'auto')}</div><div class="field"><label for="setting-dtype">Default precision</label><select class="select" id="setting-dtype" name="default_dtype">${['auto', 'float32', 'float16', 'bfloat16'].map((value) => `<option ${settings.default_dtype === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div><div class="field"><label for="setting-attn">Attention implementation</label><select class="select" id="setting-attn" name="attn_implementation">${['auto', 'native', 'sdpa', 'flash_attention_4'].map((value) => `<option ${settings.attn_implementation === value ? 'selected' : ''} value="${value}">${slugLabel(value)}</option>`).join('')}</select></div><div class="field"><label for="setting-kernel">Kernel backend</label><select class="select" id="setting-kernel" name="kernel_backend">${['auto', 'native', 'torch', 'triton', 'cuda_extension'].map((value) => `<option ${settings.kernel_backend === value ? 'selected' : ''} value="${value}">${slugLabel(value)}</option>`).join('')}</select></div><div class="field"><label for="setting-compile">Compile policy</label><select class="select" id="setting-compile" name="compile_policy">${['disabled', 'auto', 'required'].map((value) => `<option ${settings.compile_policy === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div><div class="field"><label for="setting-max-models">Maximum loaded models</label><input class="input" id="setting-max-models" name="max_loaded_models" type="number" min="1" max="8" value="${attr(settings.max_loaded_models || 1)}"></div></div></div><div class="notice">${icon('info')}<span>Auto chooses CUDA when PyTorch can access it, then MPS/XPU, and otherwise CPU. Precision remains model-aware.</span></div>${state.runtime?.models?.length ? `<div><h3 class="section-title">Loaded runtimes</h3>${state.runtime.models.map((item) => `<div class="operation-row"><span class="operation-index">${icon('gpu')}</span><div><strong>${escapeHtml(item.model_type)} · ${escapeHtml(item.device)}</strong><small>${escapeHtml(item.checkpoint)}</small></div></div>`).join('')}<button type="button" class="button danger small" style="margin-top:10px" data-action="unload-models">Unload all models</button></div>` : ''}</div>`;
}

function renderOutputSettings(settings) {
  return `${settingsHeader('Audio output', 'Format and conversion defaults for every render')}<div class="card-body"><div class="form-grid"><div class="field"><label for="setting-format">Format</label><select class="select" id="setting-format" name="output_format">${['wav', 'flac', 'mp3', 'ogg'].map((value) => `<option ${settings.output_format === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div><div class="field"><label for="setting-rate">Sample rate <small>blank keeps native</small></label><input class="input" id="setting-rate" name="output_sample_rate" type="number" min="8000" max="192000" value="${attr(settings.output_sample_rate ?? '')}" placeholder="Native"></div><div class="field"><label for="setting-channels">Channels</label><select class="select" id="setting-channels" name="output_channels"><option value="1" ${settings.output_channels === 1 ? 'selected' : ''}>Mono</option><option value="2" ${settings.output_channels === 2 ? 'selected' : ''}>Stereo</option></select></div><div class="field"><label>Audio toolkit</label><div class="path-value">${escapeHtml(state.system?.dependencies?.ffmpeg || 'FFmpeg unavailable')}</div></div></div><div class="notice">${icon('info')}<span>VoiceHub generates model-native audio first. FFmpeg performs the requested format, rate, channel, and normalization conversion afterward.</span></div></div>`;
}

function renderRuntimeSettings(settings) {
  return `${settingsHeader('Runtime & queue', 'Memory lifetime and safe background execution')}<div class="card-body"><div class="form-grid"><div class="field"><label for="setting-unload">Auto-unload after minutes <small>0 disables</small></label><input class="input" id="setting-unload" name="auto_unload_minutes" type="number" min="0" max="1440" value="${attr(settings.auto_unload_minutes ?? 15)}"></div><div class="field"><label for="setting-workers">Queue workers</label><input class="input" id="setting-workers" name="queue_workers" type="number" min="1" max="8" value="${attr(settings.queue_workers || 1)}"><p class="field-help">One is safest for a single GPU. Restart Studio after changing.</p></div><div class="field"><label for="setting-upload">Maximum upload size (MB)</label><input class="input" id="setting-upload" name="max_upload_mb" type="number" min="1" max="10000" value="${attr(settings.max_upload_mb || 500)}"></div></div><div class="notice warning">${icon('warning')}<span>Parallel GPU jobs can exceed VRAM. Increase workers only when jobs target separate devices or mostly use CPU.</span></div></div>`;
}

function renderStorageSettings(_settings, system) {
  const paths = system.app?.paths || {};
  return `${settingsHeader('Local storage', 'Database, model cache, media, and training artifacts')}<div class="card-body">${Object.entries(paths).map(([name, value]) => `<div class="field"><label>${escapeHtml(slugLabel(name))}</label><div class="path-value" title="${attr(value)}">${escapeHtml(value)}</div></div>`).join('')}<div class="notice">${icon('database')}<span>Voice metadata and job history live in SQLite. Media files remain plain files so other Linux tools can use them.</span></div></div>`;
}

function renderInterfaceSettings(settings) {
  return `${settingsHeader('Application', 'Window, browser, theme, language, and server defaults')}<div class="card-body"><div class="form-grid"><div class="field"><label for="setting-theme">Theme</label><select class="select" id="setting-theme" name="theme">${['dark', 'light', 'system'].map((value) => `<option ${settings.theme === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div><div class="field"><label for="setting-language">Language</label><select class="select" id="setting-language" name="interface_language"><option value="system" ${settings.interface_language === 'system' ? 'selected' : ''}>System language</option><option value="en" ${settings.interface_language === 'en' ? 'selected' : ''}>English</option><option value="tr" ${settings.interface_language === 'tr' ? 'selected' : ''}>Turkish (Türkçe)</option></select></div><div class="field"><label for="setting-mode">Open mode</label><select class="select" id="setting-mode" name="open_mode">${['window', 'browser', 'server'].map((value) => `<option ${settings.open_mode === value ? 'selected' : ''}>${value}</option>`).join('')}</select></div><div class="field"><label for="setting-host">Bind host</label><input class="input mono" id="setting-host" name="bind_host" value="${attr(settings.bind_host || '127.0.0.1')}"></div><div class="field"><label for="setting-port">Port</label><input class="input" id="setting-port" name="port" type="number" min="1" max="65535" value="${attr(settings.port || 8765)}"></div></div><div class="notice warning">${icon('warning')}<span>The API has no network authentication. Keep the default loopback address unless you add a trusted reverse proxy and access control.</span></div></div>`;
}

let mediaRecorder = null;
let mediaStream = null;
let recordedChunks = [];
let recordedBlob = null;
let recordStartedAt = 0;
let recordTimer = null;
let commandIndex = 0;

function openModal(content, { wide = false, command = false } = {}) {
  const layer = $('#modal-layer');
  layer.innerHTML = `<div class="modal ${wide ? 'wide' : ''} ${command ? 'command-modal' : ''}" role="dialog" aria-modal="true">${content}</div>`;
  layer.classList.add('open');
  document.body.style.overflow = 'hidden';
  hydrateIcons(layer);
  localizeTree(layer);
  requestAnimationFrame(() => $('input:not([type="hidden"]), textarea, select', layer)?.focus());
}

function closeModal() {
  stopRecording(true);
  const layer = $('#modal-layer');
  layer.classList.remove('open');
  layer.innerHTML = '';
  document.body.style.overflow = '';
}

function modalHeader(glyph, title, description) {
  return `<div class="modal-header"><span class="modal-title-icon">${icon(glyph)}</span><div><h2>${escapeHtml(title)}</h2><p>${escapeHtml(description)}</p></div><button class="icon-button modal-close" type="button" data-action="close-modal" aria-label="Close">${icon('x')}</button></div>`;
}

function showVoiceModal(voice = null, forcedKind = null) {
  const kind = forcedKind || voice?.kind || 'clone';
  const editing = Boolean(voice);
  state.voiceDraftKind = kind;
  recordedBlob = null;
  const cloneLike = ['clone', 'recording'].includes(kind);
  openModal(`
    <form id="voice-form" data-id="${attr(voice?.id || '')}">
      ${modalHeader(kind === 'design' ? 'wand' : kind === 'preset' ? 'user' : 'clone', editing ? 'Edit voice profile' : 'Add a reusable voice', 'Profiles keep compatible conditioning together and never embed audio in the database.')}
      <div class="modal-body">
        ${!editing ? `<div class="segmented" style="margin-bottom:18px">${[['clone', 'clone', 'Clone'], ['recording', 'mic', 'Record'], ['design', 'wand', 'Design'], ['preset', 'user', 'Preset']].map(([value, glyph, label]) => `<button type="button" class="${kind === value ? 'active' : ''}" data-action="voice-kind" data-kind="${value}">${icon(glyph)} ${label}</button>`).join('')}</div>` : ''}
        <input type="hidden" name="kind" value="${attr(kind)}">
        <div class="form-grid">
          <div class="field"><label for="voice-name">Name</label><input class="input" id="voice-name" name="name" value="${attr(voice?.name || '')}" placeholder="Narrator, Alex, Warm guide…" required></div>
          <div class="field"><label for="voice-language">Language</label><input class="input" id="voice-language" name="language" value="${attr(voice?.language || state.settings.default_language || 'Auto')}" placeholder="Auto"></div>
          <div class="field"><label for="voice-model">Preferred model</label><select class="select" id="voice-model" name="model_type"><option value="">Any compatible model</option>${state.models.filter((model) => kind === 'design' ? model.can_design : cloneLike ? model.can_clone : true).map((model) => `<option value="${attr(model.model_type)}" ${(voice?.model_type || state.selectedModel) === model.model_type ? 'selected' : ''}>${escapeHtml(model.display_name)}</option>`).join('')}</select></div>
          <div class="field"><label for="voice-checkpoint">Preferred checkpoint <small>optional</small></label><input class="input mono" id="voice-checkpoint" name="checkpoint" value="${attr(voice?.checkpoint || '')}" placeholder="Use current checkpoint"></div>
          ${cloneLike ? `
            <div class="field full"><label>Reference source</label><select class="select" id="voice-existing-asset" name="reference_asset_id"><option value="">Upload or record new audio</option>${state.assets.map((asset) => `<option value="${attr(asset.id)}" ${voice?.reference_asset_id === asset.id ? 'selected' : ''}>${escapeHtml(asset.name)} · ${formatDuration(asset.duration)}</option>`).join('')}</select></div>
            ${kind === 'clone' ? `<div class="field full"><label>Import a clean reference</label><label class="drop-zone" id="voice-drop-zone"><input type="file" id="voice-file" accept="audio/*"><span class="drop-zone-icon">${icon('upload')}</span><strong id="voice-file-label">Drop audio here or click to browse</strong><small>10–30 seconds of clean, single-speaker speech works best</small></label></div>` : `<div class="field full"><label>Record a clean reference</label><div class="record-panel"><button class="record-button" type="button" data-action="toggle-record" aria-label="Record">${icon('mic')}</button><div class="record-copy"><strong id="record-title">Ready to record</strong><small id="record-copy">Use a quiet room and speak naturally for 10–30 seconds.</small></div><span class="badge" id="record-time">0:00</span></div></div>`}
            <div class="field full"><label for="voice-reference-text">Reference transcript <small>strongly recommended</small></label><textarea class="textarea" id="voice-reference-text" name="reference_text" placeholder="Type exactly what is spoken in the reference…">${escapeHtml(voice?.reference_text || '')}</textarea></div>
            <label class="checkbox-row span-full"><input type="checkbox" id="voice-consent" name="consent_confirmed" ${voice?.consent_confirmed ? 'checked' : ''} required><span><strong>I have the speaker's authorization</strong><small>Only clone your own voice or a voice you have explicit permission to use.</small></span></label>
            <div class="field full"><label for="voice-consent-note">Authorization note <small>optional, stored locally</small></label><input class="input" id="voice-consent-note" name="consent_note" value="${attr(voice?.consent_note || '')}" placeholder="Self recording, signed release, project agreement…"></div>` : ''}
          ${kind === 'design' ? `<div class="field full"><label for="voice-design">Voice design description</label><textarea class="textarea" id="voice-design" name="design_prompt" required placeholder="A calm, mature documentary narrator with a soft Turkish accent, close-mic warmth, and deliberate pacing…">${escapeHtml(voice?.design_prompt || '')}</textarea><p class="field-help">Describe age, timbre, accent, pace, emotion, recording style, and delivery. Compatible models translate this prompt differently.</p></div>` : ''}
          ${kind === 'preset' ? `<div class="field full"><label for="voice-speaker">Model speaker / voice name</label><input class="input" id="voice-speaker" name="speaker" value="${attr(voice?.speaker || '')}" required placeholder="Vivian, af_heart, speaker_0…"><p class="field-help">Use the exact speaker identifier expected by the selected model.</p></div>` : ''}
          <div class="field full"><label for="voice-tags">Tags <small>comma separated</small></label><input class="input" id="voice-tags" name="tags" value="${attr((voice?.tags || []).join(', '))}" placeholder="narration, warm, English"></div>
          <div class="field full"><label for="voice-conditioning">Additional conditioning <small>JSON, optional</small></label><textarea class="textarea mono" id="voice-conditioning" name="conditioning">${escapeHtml(JSON.stringify(voice?.conditioning || {}, null, 2))}</textarea></div>
        </div>
      </div>
      <div class="modal-footer">${editing ? `<button class="button danger" type="button" data-action="delete-voice" data-id="${attr(voice.id)}">${icon('trash')} Delete</button>` : ''}<button class="button secondary" type="button" data-action="close-modal">Cancel</button><button class="button" type="submit">${icon('save')} ${editing ? 'Save changes' : 'Create voice'}</button></div>
    </form>`, { wide: true });
}

function showUploadModal() {
  openModal(`<form id="upload-form">${modalHeader('upload', 'Import audio', 'Files are copied into the local Studio library and analyzed with FFprobe.')}<div class="modal-body"><div class="form-grid"><div class="field full"><label class="drop-zone"><input type="file" id="upload-file" accept="audio/*" required><span class="drop-zone-icon">${icon('upload')}</span><strong id="upload-file-label">Drop audio here or click to browse</strong><small>WAV, FLAC, MP3, OGG, AAC, M4A, OPUS, WEBM, and FFmpeg-readable audio</small></label></div><div class="field"><label for="upload-name">Library name <small>optional</small></label><input class="input" id="upload-name" name="name" placeholder="Uses the filename"></div><div class="field"><label for="upload-kind">Asset type</label><select class="select" id="upload-kind" name="kind"><option value="audio">Audio</option><option value="reference">Voice reference</option><option value="dataset">Dataset sample</option><option value="music">Music / ambience</option></select></div></div></div><div class="modal-footer"><button class="button secondary" type="button" data-action="close-modal">Cancel</button><button class="button" type="submit">${icon('upload')} Import</button></div></form>`);
}

function showConcatModal() {
  openModal(`<form id="concat-form">${modalHeader('layers', 'Combine audio assets', 'Join selected clips in order, with an optional equal-power crossfade.')}<div class="modal-body"><div class="form-grid"><div class="field full"><label>Clips <small>select at least two in playback order</small></label><div class="asset-list card" style="max-height:260px">${state.assets.map((asset, index) => `<label class="asset-row"><input type="checkbox" name="asset_ids" value="${attr(asset.id)}"><span class="asset-kind">${icon('waveform')}</span><span class="asset-copy"><strong>${escapeHtml(asset.name)}</strong><small>${formatDuration(asset.duration)}</small></span><span class="badge">${index + 1}</span></label>`).join('')}</div></div><div class="field"><label for="concat-name">Output name</label><input class="input" id="concat-name" value="Combined audio" required></div><div class="field"><label for="concat-crossfade">Crossfade (seconds)</label><input class="input" id="concat-crossfade" type="number" min="0" max="10" step="0.01" value="0"></div><div class="field"><label for="concat-format">Output format</label><select class="select" id="concat-format">${['wav', 'flac', 'mp3', 'ogg'].map((format) => `<option ${state.settings.output_format === format ? 'selected' : ''}>${format}</option>`).join('')}</select></div></div></div><div class="modal-footer"><button class="button secondary" type="button" data-action="close-modal">Cancel</button><button class="button" type="submit">${icon('layers')} Combine clips</button></div></form>`, { wide: true });
}

const EFFECT_FORMS = {
  gain: { label: 'Gain (dB)', key: 'db', min: -60, max: 30, step: .1, value: 3 },
  speed: { label: 'Tempo multiplier', key: 'factor', min: .25, max: 4, step: .01, value: 1.1 },
  pitch: { label: 'Pitch shift (semitones)', key: 'semitones', min: -24, max: 24, step: .1, value: 2 },
  fade_in: { label: 'Fade duration (seconds)', key: 'duration', min: 0, max: 60, step: .01, value: .25 },
  fade_out: { label: 'Fade duration (seconds)', key: 'duration', min: 0, max: 60, step: .01, value: .25 },
  highpass: { label: 'Cutoff frequency (Hz)', key: 'frequency', min: 20, max: 20000, step: 1, value: 80 },
  lowpass: { label: 'Cutoff frequency (Hz)', key: 'frequency', min: 20, max: 20000, step: 1, value: 12000 },
};

function addEffect(effect) {
  const immediate = {
    normalize: { op: 'normalize', target_lufs: -16, true_peak: -1.5 },
    denoise: { op: 'denoise', strength: 10 },
    trim_silence: { op: 'trim_silence', threshold_db: -42, minimum_seconds: .2 },
    compress: { op: 'compress', threshold_db: -18, ratio: 3 },
    reverse: { op: 'reverse' },
  }[effect];
  if (immediate) {
    state.editor.operations.push(immediate); render(); toast(`${slugLabel(effect)} added to the operation stack.`, 'info'); return;
  }
  const spec = EFFECT_FORMS[effect];
  if (!spec) return;
  openModal(`<form id="effect-form" data-effect="${attr(effect)}" data-key="${attr(spec.key)}">${modalHeader('sliders', slugLabel(effect), 'This effect will be added to the non-destructive operation stack.')}<div class="modal-body"><div class="field"><label for="effect-value">${escapeHtml(spec.label)}</label><input class="input" id="effect-value" type="number" min="${spec.min}" max="${spec.max}" step="${spec.step}" value="${spec.value}" required></div></div><div class="modal-footer"><button class="button secondary" type="button" data-action="close-modal">Cancel</button><button class="button" type="submit">Add effect</button></div></form>`);
}

async function showModelDetails(modelType) {
  openModal(`${modalHeader('blocks', 'Inspecting model', 'Reading the VoiceHub adapter signature…')}<div class="modal-body">${emptyState('activity', 'Discovering controls', 'No checkpoint is loaded during introspection.')}</div>`);
  try {
    const schema = state.online ? await api(`/api/models/${encodeURIComponent(modelType)}`) : fallbackSchema(state.models.find((model) => model.model_type === modelType));
    const model = schema.model;
    const fields = [...schema.conditioning, ...schema.generation, ...schema.model_config];
    openModal(`${modalHeader('blocks', model.display_name, model.default_checkpoint)}<div class="modal-body"><div class="chip-row" style="margin-bottom:16px">${(model.capabilities || []).map((cap) => `<span class="capability-chip">${escapeHtml(slugLabel(cap))}</span>`).join('')}</div><div class="form-grid three"><div class="metric"><strong>${fields.length}</strong><small>Discovered controls</small></div><div class="metric"><strong>${escapeHtml(schema.training?.support || 'unknown')}</strong><small>Training</small></div><div class="metric"><strong>${model.native ? 'Native' : 'Adapter'}</strong><small>Integration</small></div></div>${schema.introspection_error ? `<div class="notice warning" style="margin-top:16px">${icon('warning')}<span>${escapeHtml(schema.introspection_error)}</span></div>` : ''}<h3 class="section-title" style="margin-top:20px">Generation signature</h3><div class="operation-stack" style="padding:0;min-height:0">${fields.map((field, index) => `<div class="operation-row"><span class="operation-index">${index + 1}</span><div><strong>${escapeHtml(field.label)}</strong><small>${escapeHtml(field.name)} · ${escapeHtml(field.source)} · ${escapeHtml(field.type || 'any')}</small></div><span class="badge">${escapeHtml(field.control)}</span></div>`).join('')}</div></div><div class="modal-footer"><a class="button secondary" href="${attr(model.docs_url)}" target="_blank" rel="noreferrer">${icon('external')} VoiceHub docs</a><button class="button" data-action="use-model" data-model="${attr(modelType)}">Use model</button></div>`, { wide: true });
  } catch (error) { closeModal(); toast(error.message, 'error'); }
}

function showCommandPalette(query = '') {
  const actions = [
    ['generate', 'sparkles', 'Generate speech', 'Open the synthesis composer'],
    ['voices', 'voices', 'Add or manage voices', 'Clone, record, design, and presets'],
    ['editor', 'waveform', 'Edit audio', 'Cut and process local audio'],
    ['models', 'blocks', 'Browse model library', `${state.models.length} VoiceHub adapters`],
    ['training', 'sliders', 'Start a fine-tune', 'VoiceHub training adapters'],
    ['queue', 'queue', 'Open job queue', 'Background work and errors'],
    ['settings', 'settings', 'Open settings', 'Compute and output defaults'],
  ];
  const needle = query.toLowerCase();
  const matchingModels = state.models.filter((model) => !needle || [model.display_name, model.model_type].join(' ').toLowerCase().includes(needle)).slice(0, 10);
  const matchingActions = actions.filter((item) => !needle || item.join(' ').toLowerCase().includes(needle));
  commandIndex = 0;
  openModal(`<div class="command-input-wrap">${icon('search')}<input class="command-input" id="command-input" value="${attr(query)}" autocomplete="off" placeholder="Search models and actions…"></div><div class="command-results" id="command-results"><p class="command-group-label">Actions</p>${matchingActions.map(([route, glyph, title, copy], index) => `<button class="command-item ${index === 0 ? 'active' : ''}" data-action="command-route" data-route="${route}"><span class="command-item-icon">${icon(glyph)}</span><div><strong>${title}</strong><small>${copy}</small></div></button>`).join('')}${matchingModels.length ? `<p class="command-group-label">Models</p>${matchingModels.map((model) => `<button class="command-item" data-action="command-model" data-model="${attr(model.model_type)}"><span class="command-item-icon">${escapeHtml(model.display_name.slice(0, 2).toUpperCase())}</span><div><strong>${escapeHtml(model.display_name)}</strong><small>${escapeHtml(model.default_checkpoint)}</small></div><kbd>Use</kbd></button>`).join('')}` : ''}</div>`, { command: true });
  $('#command-input')?.focus();
}

function toast(message, type = 'info') {
  const region = $('#toast-region');
  const element = document.createElement('div');
  element.className = `toast ${type}`;
  element.innerHTML = `<span class="toast-icon">${icon(type === 'error' ? 'warning' : type === 'success' ? 'check' : 'info')}</span><div class="toast-copy"><strong>${t(type === 'error' ? 'Something needs attention' : type === 'success' ? 'Done' : 'VoiceHub Studio')}</strong><p>${escapeHtml(t(message))}</p></div><button class="toast-close" aria-label="Dismiss">${icon('x')}</button>`;
  region.appendChild(element);
  localizeTree(element);
  $('.toast-close', element).addEventListener('click', () => element.remove());
  setTimeout(() => element.remove(), type === 'error' ? 9000 : 4500);
}

function navigate(route) {
  if (!(route in ROUTES)) return;
  if (location.hash !== `#${route}`) location.hash = route;
  else { state.route = route; render(); }
  closeMobileNav();
}

function closeMobileNav() {
  document.body.classList.remove('nav-open');
}

function parseJsonArea(id, label) {
  const value = $(id)?.value.trim();
  if (!value) return {};
  try {
    const parsed = JSON.parse(value);
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('must be a JSON object');
    return parsed;
  } catch (error) { throw new Error(`${label}: ${error.message}`); }
}

function readDynamicFields(form) {
  const groups = { generation_config: {}, model_kwargs: {}, model_config: {} };
  $$('[data-dynamic-field]', form).forEach((input) => {
    if (input.disabled) return;
    let value;
    if (input.dataset.structuredValue === 'true') {
      if (!input.value.trim()) return;
      try { value = JSON.parse(input.value); } catch (error) { throw new Error(`${input.dataset.fieldName} must be valid JSON: ${error.message}`); }
    }
    else if (input.dataset.nullableBoolean === 'true') value = input.value === '' ? null : input.value === 'true';
    else if (input.type === 'checkbox') value = input.checked;
    else if (input.type === 'number' || input.type === 'range') value = input.value === '' ? null : Number(input.value);
    else value = input.value.trim();
    if (value === '' || value == null) return;
    groups[input.dataset.fieldSource][input.dataset.fieldName] = value;
  });
  return groups;
}

function setBusy(form, busy, copy = 'Working…') {
  const button = $('button[type="submit"]', form);
  if (!button) return;
  if (busy) { button.dataset.previousHtml = button.innerHTML; button.innerHTML = t(copy); button.classList.add('loading'); button.disabled = true; }
  else { button.innerHTML = button.dataset.previousHtml || button.innerHTML; button.classList.remove('loading'); button.disabled = false; }
}

async function submitGeneration(form) {
  if (!state.online) throw new Error('Start the local VoiceHub Studio service before generating.');
  const dynamic = readDynamicFields(form);
  Object.assign(dynamic.model_kwargs, parseJsonArea('#advanced-model-json', 'Model keyword JSON'));
  Object.assign(dynamic.model_config, parseJsonArea('#advanced-config-json', 'Model config JSON'));
  Object.assign(dynamic.generation_config, parseJsonArea('#advanced-generation-json', 'Generation JSON'));
  const supportsMode = state.schema?.conditioning?.some((field) => field.name === 'mode');
  if (supportsMode) dynamic.model_kwargs.mode = state.generationMode === 'clone' ? 'voice_clone' : state.generationMode === 'design' ? 'voice_design' : 'custom_voice';
  const selectedVoice = state.voices.find((voice) => voice.id === ($('#gen-voice').value || null));
  if (state.generationMode === 'clone' && !['clone', 'recording'].includes(selectedVoice?.kind)) {
    const hasReference = state.schema?.conditioning?.some((field) => field.control === 'asset' && dynamic.model_kwargs[field.name]);
    if (!hasReference) throw new Error('Choose reference audio or select a saved clone voice.');
  }
  if (state.generationMode === 'design' && selectedVoice?.kind !== 'design') {
    const hasDescription = ['instruct', 'instruction', 'description', 'voice_description'].some((name) => String(dynamic.model_kwargs[name] || '').trim());
    if (!hasDescription) throw new Error('Describe the voice to design or select a saved designed voice.');
  }
  const rateValue = $('#gen-rate')?.value;
  const payload = {
    text: $('#generation-text').value.trim(),
    model_type: $('#gen-model').value,
    checkpoint: $('#gen-checkpoint').value.trim(),
    voice_id: $('#gen-voice').value || null,
    device: $('#gen-device')?.value || state.settings.default_device || 'auto',
    dtype: $('#gen-dtype')?.value || state.settings.default_dtype || 'auto',
    generation_config: dynamic.generation_config,
    model_kwargs: dynamic.model_kwargs,
    model_config: dynamic.model_config,
    optimization: {
      attn_implementation: state.settings.attn_implementation || 'auto',
      kernel_backend: state.settings.kernel_backend || 'auto',
      compile_policy: state.settings.compile_policy || 'disabled',
    },
    output_format: $('#gen-format')?.value || state.settings.output_format || 'wav',
    output_sample_rate: rateValue ? Number(rateValue) : null,
    output_channels: Number($('#gen-channels')?.value || state.settings.output_channels || 1),
    normalize_output: Boolean($('#gen-normalize')?.checked),
  };
  if (!payload.text) throw new Error('Write a script before generating.');
  if (!payload.checkpoint) throw new Error('A model checkpoint is required.');
  setBusy(form, true, 'Queued…');
  try {
    const result = await api('/api/generations', { method: 'POST', body: JSON.stringify(payload) });
    state.generations.unshift(result.generation);
    state.jobs.unshift(result.job);
    state.selectedGenerationId = result.generation.id;
    updateChrome(); render();
    toast('Speech generation was added to the local queue.', 'success');
  } finally { if (form.isConnected) setBusy(form, false); }
}

async function uploadAudio(file, name = '', kind = 'audio') {
  const body = new FormData();
  body.append('file', file, file.name || `recording-${Date.now()}.webm`);
  if (name) body.append('name', name);
  body.append('kind', kind);
  return api('/api/assets', { method: 'POST', body });
}

async function submitVoice(form) {
  const editingId = form.dataset.id || null;
  const kind = $('[name="kind"]', form).value;
  let referenceAssetId = $('#voice-existing-asset', form)?.value || null;
  const file = $('#voice-file', form)?.files?.[0] || recordedBlob;
  setBusy(form, true, file ? 'Importing audio…' : 'Saving…');
  try {
    if (file) {
      const uploaded = await uploadAudio(file, `${$('#voice-name').value.trim()} reference`, 'reference');
      state.assets.unshift(uploaded);
      referenceAssetId = uploaded.id;
    }
    const payload = {
      name: $('#voice-name').value.trim(), kind,
      model_type: $('#voice-model').value || null,
      checkpoint: $('#voice-checkpoint').value.trim() || null,
      language: $('#voice-language').value.trim() || null,
      speaker: $('#voice-speaker', form)?.value.trim() || null,
      reference_asset_id: referenceAssetId,
      reference_text: $('#voice-reference-text', form)?.value.trim() || null,
      design_prompt: $('#voice-design', form)?.value.trim() || null,
      conditioning: parseJsonArea('#voice-conditioning', 'Conditioning JSON'),
      tags: $('#voice-tags').value.split(',').map((tag) => tag.trim()).filter(Boolean),
      consent_confirmed: Boolean($('#voice-consent', form)?.checked),
      consent_note: $('#voice-consent-note', form)?.value.trim() || null,
    };
    if (editingId) delete payload.kind;
    const voice = await api(editingId ? `/api/voices/${encodeURIComponent(editingId)}` : '/api/voices', { method: editingId ? 'PATCH' : 'POST', body: JSON.stringify(payload) });
    const index = state.voices.findIndex((item) => item.id === voice.id);
    if (index >= 0) state.voices[index] = voice; else state.voices.unshift(voice);
    closeModal(); render(); toast(editingId ? 'Voice profile updated.' : 'Voice profile created.', 'success');
  } finally { if (form.isConnected) setBusy(form, false); }
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') throw new Error('This browser shell does not expose microphone recording. Import an audio file instead.');
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: false } });
  recordedChunks = []; recordedBlob = null;
  const preferred = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/webm'].find((type) => MediaRecorder.isTypeSupported(type));
  mediaRecorder = new MediaRecorder(mediaStream, preferred ? { mimeType: preferred } : undefined);
  mediaRecorder.addEventListener('dataavailable', (event) => { if (event.data.size) recordedChunks.push(event.data); });
  mediaRecorder.addEventListener('stop', () => {
    recordedBlob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
    Object.defineProperty(recordedBlob, 'name', { value: `reference-${Date.now()}.webm` });
    $('#record-title') && ($('#record-title').textContent = 'Reference captured');
    $('#record-copy') && ($('#record-copy').textContent = `${formatBytes(recordedBlob.size)} ready to save`);
  });
  mediaRecorder.start(250); recordStartedAt = Date.now();
  $('.record-button')?.classList.add('recording');
  $('#record-title') && ($('#record-title').textContent = 'Recording…');
  recordTimer = setInterval(() => {
    const seconds = Math.floor((Date.now() - recordStartedAt) / 1000);
    const label = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
    $('#record-time') && ($('#record-time').textContent = label);
  }, 250);
}

function stopRecording(discard = false) {
  if (recordTimer) clearInterval(recordTimer);
  recordTimer = null;
  if (mediaRecorder?.state === 'recording') mediaRecorder.stop();
  mediaStream?.getTracks().forEach((track) => track.stop());
  mediaStream = null;
  $('.record-button')?.classList.remove('recording');
  if (discard) { recordedBlob = null; recordedChunks = []; }
}

async function applyEdits() {
  const asset = currentAsset();
  if (!asset || !state.editor.operations.length) return;
  const payload = { source_asset_id: asset.id, name: `${asset.name} edit`, operations: state.editor.operations, output_format: state.settings.output_format || 'wav', sample_rate: state.settings.output_sample_rate, channels: state.settings.output_channels };
  const job = await api('/api/audio/edit', { method: 'POST', body: JSON.stringify(payload) });
  state.jobs.unshift(job); state.editor.operations = []; updateChrome(); render(); toast('Non-destructive audio edit queued.', 'success');
}

async function selectAsset(assetId) {
  state.editor.assetId = assetId; state.editor.peaks = null; state.editor.operations = [];
  const asset = currentAsset(); state.editor.start = 0; state.editor.end = Number(asset?.duration || 0);
  render();
  if (asset && state.online) {
    try { state.editor.peaks = await api(`/api/assets/${encodeURIComponent(asset.id)}/waveform?buckets=1600`); prepareWaveform(); }
    catch (error) { toast(`Waveform analysis failed: ${error.message}`, 'error'); }
  }
}

async function loadModel(modelType) {
  const model = state.models.find((item) => item.model_type === modelType);
  if (!model) return;
  const result = await api(`/api/models/${encodeURIComponent(modelType)}/load`, { method: 'POST', body: JSON.stringify({ checkpoint: model.default_checkpoint, device: state.settings.default_device || 'auto', dtype: state.settings.default_dtype || 'auto', model_config: {}, optimization: { attn_implementation: state.settings.attn_implementation || 'auto', kernel_backend: state.settings.kernel_backend || 'auto', compile_policy: state.settings.compile_policy || 'disabled' } }) });
  state.jobs.unshift(result); updateChrome(); render(); toast(`${model.display_name} is loading in the background.`, 'success');
}

async function enableTurkishMode(modelType = TURKISH_DEFAULT.model_type) {
  const model = state.models.find((item) => item.model_type === modelType && item.supports_turkish)
    || state.models.find((item) => item.model_type === TURKISH_DEFAULT.model_type)
    || state.models.find((item) => item.supports_turkish);
  if (!model) throw new Error('No Turkish-capable model is available in this VoiceHub installation.');
  const preset = model.turkish || TURKISH_DEFAULT;
  state.selectedVoiceId = null;
  state.generationMode = preset.requires_reference ? 'clone' : 'synthesize';
  state.checkpointOverride = preset.checkpoint || model.default_checkpoint;
  if (!state.generationText || Object.values(DEFAULT_SCRIPTS).includes(state.generationText)) {
    state.generationText = DEFAULT_SCRIPTS.tr;
  }
  Object.assign(state.settings, {
    default_model_type: model.model_type,
    default_checkpoint: state.checkpointOverride,
    default_language: preset.language || 'tr',
  });
  await loadModelSchema(model.model_type, false);
  if (state.online) {
    state.settings = await api('/api/settings', {
      method: 'PUT',
      body: JSON.stringify({
        default_model_type: model.model_type,
        default_checkpoint: state.checkpointOverride,
        default_language: preset.language || 'tr',
      }),
    });
  }
  navigate('generate');
  render();
  toast('Turkish speech mode is ready.', 'success');
}

async function refreshCollections() {
  if (!state.online) return;
  try {
    const [voices, assets, generations, jobs, training, runtime] = await Promise.all([api('/api/voices'), api('/api/assets'), api('/api/generations'), api('/api/jobs'), api('/api/training'), api('/api/runtime')]);
    Object.assign(state, { voices: voices.items, assets: assets.items, generations: generations.items, jobs: jobs.items, training: training.items, runtime });
    if (state.editor.assetId && !state.assets.some((asset) => asset.id === state.editor.assetId)) state.editor.assetId = state.assets[0]?.id || null;
    updateChrome(); render();
  } catch (_) { /* transient refresh failure; primary API calls surface errors */ }
}

document.addEventListener('click', async (event) => {
  const target = event.target.closest('[data-action]');
  if (!target) return;
  const action = target.dataset.action;
  try {
    if (action === 'close-modal') closeModal();
    else if (action === 'open-models') navigate('models');
    else if (action === 'turkish-mode') await enableTurkishMode();
    else if (action === 'use-turkish-model') await enableTurkishMode(target.dataset.model);
    else if (action === 'go-queue') navigate('queue');
    else if (action === 'generation-mode') {
      const mode = target.dataset.mode;
      const currentCheckpoint = $('#gen-checkpoint')?.value.trim() || '';
      const selectedProfile = state.voices.find((voice) => voice.id === state.selectedVoiceId);
      const compatible = CHECKPOINT_VARIANTS[state.selectedModel]?.[mode];
      if (selectedProfile?.checkpoint) state.checkpointOverride = selectedProfile.checkpoint;
      else if (compatible && (!currentCheckpoint || currentCheckpoint.startsWith('Qwen/Qwen3-TTS-12Hz-'))) state.checkpointOverride = compatible;
      else state.checkpointOverride = currentCheckpoint || null;
      state.generationMode = mode; render();
    }
    else if (action === 'select-generation') { state.selectedGenerationId = target.dataset.id; render(); }
    else if (action === 'new-voice') showVoiceModal();
    else if (action === 'voice-kind') showVoiceModal(null, target.dataset.kind);
    else if (action === 'edit-voice') showVoiceModal(state.voices.find((voice) => voice.id === target.dataset.id));
    else if (action === 'favorite-voice') {
      const voice = state.voices.find((item) => item.id === target.dataset.id);
      if (voice) { const updated = await api(`/api/voices/${encodeURIComponent(voice.id)}`, { method: 'PATCH', body: JSON.stringify({ favorite: !voice.favorite }) }); Object.assign(voice, updated); render(); }
    }
    else if (action === 'use-voice') {
      const voice = state.voices.find((item) => item.id === target.dataset.id);
      state.selectedVoiceId = target.dataset.id;
      if (voice?.model_type && state.models.some((model) => model.model_type === voice.model_type)) await loadModelSchema(voice.model_type, false);
      state.generationMode = voice?.kind === 'design' ? 'design' : ['clone', 'recording'].includes(voice?.kind) ? 'clone' : 'synthesize';
      state.checkpointOverride = voice?.checkpoint || CHECKPOINT_VARIANTS[state.selectedModel]?.[state.generationMode] || null;
      closeModal(); navigate('generate'); toast(`${voice?.name || 'Voice'} selected.`, 'success');
    }
    else if (action === 'preview-voice') { const player = new Audio(target.dataset.url); player.play().catch((error) => toast(error.message, 'error')); }
    else if (action === 'delete-voice') {
      const voice = state.voices.find((item) => item.id === target.dataset.id);
      if (voice && window.confirm(`Delete the voice profile “${voice.name}”? The reference audio asset will remain in the library.`)) {
        await api(`/api/voices/${encodeURIComponent(voice.id)}`, { method: 'DELETE' }); state.voices = state.voices.filter((item) => item.id !== voice.id); closeModal(); render(); toast('Voice profile deleted.', 'success');
      }
    }
    else if (action === 'upload-audio') showUploadModal();
    else if (action === 'concat-assets') showConcatModal();
    else if (action === 'select-asset') await selectAsset(target.dataset.id);
    else if (action === 'delete-asset') {
      const asset = state.assets.find((item) => item.id === target.dataset.id);
      if (asset && window.confirm(`Permanently delete “${asset.name}” and its local audio file?`)) {
        await api(`/api/assets/${encodeURIComponent(asset.id)}`, { method: 'DELETE' }); state.assets = state.assets.filter((item) => item.id !== asset.id); state.editor.assetId = state.assets[0]?.id || null; state.editor.operations = []; render(); toast('Audio asset and local file deleted.', 'success');
      }
    }
    else if (action === 'add-effect') addEffect(target.dataset.effect);
    else if (action === 'remove-operation') { state.editor.operations.splice(Number(target.dataset.index), 1); render(); }
    else if (action === 'clear-operations') { state.editor.operations = []; render(); }
    else if (action === 'keep-selection') {
      const asset = currentAsset(); const start = state.editor.start; const end = state.editor.end || asset?.duration;
      if (!asset || end - start < .01) throw new Error('Drag across the waveform to choose a non-empty range.');
      state.editor.operations.push({ op: 'trim', start: Number(start.toFixed(6)), end: Number(end.toFixed(6)) }); render(); toast('Keep-range added to the stack.', 'info');
    }
    else if (action === 'delete-selection') {
      const asset = currentAsset(); const start = state.editor.start; const end = state.editor.end || asset?.duration;
      if (!asset || end - start < .01) throw new Error('Drag across the waveform to choose a non-empty range.');
      state.editor.operations.push({ op: 'remove_range', start: Number(start.toFixed(6)), end: Number(end.toFixed(6)) }); render(); toast('Cut added to the stack.', 'info');
    }
    else if (action === 'auto-segments') {
      const asset = currentAsset(); if (!asset) return;
      target.classList.add('loading'); target.disabled = true;
      const result = await api(`/api/assets/${encodeURIComponent(asset.id)}/segments`);
      state.editor.operations.push({ op: 'keep_ranges', ranges: result.segments }); render(); toast(`${result.segments.length} speech regions detected.`, 'success');
    }
    else if (action === 'apply-edits') await applyEdits();
    else if (action === 'play-asset') {
      const audio = $('#editor-audio'); if (!audio) return;
      if (audio.paused) { await audio.play(); target.innerHTML = icon('pause'); } else { audio.pause(); target.innerHTML = icon('play'); }
    }
    else if (action === 'stop-asset') { const audio = $('#editor-audio'); if (audio) { audio.pause(); audio.currentTime = 0; } }
    else if (action === 'preview-selection') {
      const audio = $('#editor-audio'); if (!audio) return;
      audio.currentTime = state.editor.start; audio.dataset.stopAt = state.editor.end || currentAsset()?.duration || 0; await audio.play();
    }
    else if (action === 'model-filter') { state.modelFilter = target.dataset.filter; render(); }
    else if (action === 'voice-filter') { state.voiceFilter = target.dataset.filter; render(); }
    else if (action === 'queue-filter') { state.queueFilter = target.dataset.filter; render(); }
    else if (action === 'settings-tab') { state.settingsTab = target.dataset.tab; render(); }
    else if (action === 'model-details') await showModelDetails(target.dataset.model);
    else if (action === 'load-model') await loadModel(target.dataset.model);
    else if (action === 'use-model' || action === 'command-model') {
      const modelType = target.dataset.model; state.checkpointOverride = null; state.selectedVoiceId = null; closeModal(); await loadModelSchema(modelType, false); navigate('generate');
    }
    else if (action === 'cancel-job') { await api(`/api/jobs/${encodeURIComponent(target.dataset.id)}/cancel`, { method: 'POST' }); await refreshCollections(); toast('Cancellation requested.', 'success'); }
    else if (action === 'refresh-workspace') { await loadWorkspace({ quiet: true }); toast('Workspace refreshed.', 'success'); }
    else if (action === 'unload-models') { const result = await api('/api/runtime', { method: 'DELETE' }); state.runtime = result; render(); toast(`${result.removed} runtime${result.removed === 1 ? '' : 's'} unloaded.`, 'success'); }
    else if (action === 'toggle-record') { if (mediaRecorder?.state === 'recording') stopRecording(); else await startRecording(); }
    else if (action === 'command-route') { closeModal(); navigate(target.dataset.route); }
  } catch (error) { target.classList.remove('loading'); target.disabled = false; toast(error.message, 'error'); }
});

document.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;
  try {
    if (form.id === 'generation-form') await submitGeneration(form);
    else if (form.id === 'voice-form') await submitVoice(form);
    else if (form.id === 'upload-form') {
      const file = $('#upload-file', form).files[0]; if (!file) throw new Error('Choose an audio file first.');
      setBusy(form, true, 'Importing…');
      const asset = await uploadAudio(file, $('#upload-name', form).value.trim(), $('#upload-kind', form).value);
      state.assets.unshift(asset); state.editor.assetId = asset.id; state.editor.peaks = null; closeModal(); navigate('editor'); await selectAsset(asset.id); toast('Audio imported into the local library.', 'success');
    }
    else if (form.id === 'concat-form') {
      const ids = $$('input[name="asset_ids"]:checked', form).map((input) => input.value);
      if (ids.length < 2) throw new Error('Select at least two audio assets.');
      setBusy(form, true, 'Queueing…');
      const job = await api('/api/audio/concat', { method: 'POST', body: JSON.stringify({ asset_ids: ids, name: $('#concat-name').value.trim(), crossfade: Number($('#concat-crossfade').value), output_format: $('#concat-format').value }) });
      state.jobs.unshift(job); closeModal(); updateChrome(); navigate('queue'); toast('Audio combination queued.', 'success');
    }
    else if (form.id === 'effect-form') {
      const operation = { op: form.dataset.effect, [form.dataset.key]: Number($('#effect-value', form).value) };
      state.editor.operations.push(operation); closeModal(); render(); toast(`${slugLabel(operation.op)} added to the stack.`, 'info');
    }
    else if (form.id === 'training-form') await submitTraining(form);
    else if (form.id === 'settings-form') await submitSettings(form);
  } catch (error) { if (form.isConnected) setBusy(form, false); toast(error.message, 'error'); }
});

document.addEventListener('change', async (event) => {
  const input = event.target;
  try {
    if (input.id === 'gen-model') { state.checkpointOverride = null; await loadModelSchema(input.value); }
    else if (input.id === 'gen-voice') {
      state.selectedVoiceId = input.value || null;
      const voice = state.voices.find((item) => item.id === state.selectedVoiceId);
      if (voice?.checkpoint) state.checkpointOverride = voice.checkpoint;
      if (voice?.kind === 'design') state.generationMode = 'design';
      else if (['clone', 'recording'].includes(voice?.kind)) state.generationMode = 'clone';
      else if (voice?.kind === 'preset') state.generationMode = 'synthesize';
      if (voice && !voice.checkpoint) state.checkpointOverride = CHECKPOINT_VARIANTS[state.selectedModel]?.[state.generationMode] || state.checkpointOverride;
      if (voice) render();
    }
    else if (input.id === 'train-model') await loadModelSchema(input.value);
    else if (input.dataset.rangeEnable) {
      const range = document.getElementById(input.dataset.rangeEnable);
      if (range) {
        range.disabled = !input.checked;
        const label = input.closest('.range-value')?.querySelector('span');
        if (label) label.textContent = input.checked ? range.value : 'Auto';
      }
    }
    else if (input.id === 'voice-file' || input.id === 'upload-file') {
      const file = input.files?.[0];
      const label = input.id === 'voice-file' ? $('#voice-file-label') : $('#upload-file-label');
      if (label && file) label.textContent = `${file.name} · ${formatBytes(file.size)}`;
    }
  } catch (error) { toast(error.message, 'error'); }
});

let searchTimer = null;
document.addEventListener('input', (event) => {
  const input = event.target;
  if (input.id === 'generation-text') {
    state.generationText = input.value;
    const words = input.value.trim() ? input.value.trim().split(/\s+/).length : 0;
    $('#script-words').textContent = t(`${words.toLocaleString()} words`);
    $('#script-chars').textContent = `${input.value.length.toLocaleString()} / 200,000`;
  } else if (input.id === 'gen-checkpoint') {
    state.checkpointOverride = input.value;
  } else if (input.matches('input[type="range"][data-dynamic-field]')) {
    const label = input.closest('.range-wrap')?.querySelector('.range-value span');
    if (label) label.textContent = input.value;
  } else if (input.id === 'model-search' || input.id === 'voice-search') {
    clearTimeout(searchTimer);
    const key = input.id === 'model-search' ? 'modelSearch' : 'voiceSearch'; state[key] = input.value;
    searchTimer = setTimeout(() => { render(); const replacement = $(`#${input.id}`); replacement?.focus(); replacement?.setSelectionRange(replacement.value.length, replacement.value.length); }, 140);
  } else if (input.id === 'command-input') {
    clearTimeout(searchTimer); searchTimer = setTimeout(() => showCommandPalette(input.value), 80);
  }
});

async function submitTraining(form) {
  const custom = parseJsonArea('#train-config-json', 'Training overrides');
  const trainingArguments = {
    max_steps: Number($('#train-steps').value),
    per_device_train_batch_size: Number($('#train-batch').value),
    per_device_eval_batch_size: Number($('#train-batch').value),
    learning_rate: Number($('#train-lr').value),
    gradient_accumulation_steps: Number($('#train-grad-accum').value),
    save_steps: Number($('#train-save-steps').value),
    logging_steps: Number($('#train-log-steps').value),
    ...(custom.training_arguments || custom),
  };
  const payload = {
    name: $('#train-name').value.trim(), model_type: $('#train-model').value,
    checkpoint: $('#train-checkpoint').value.trim(), train_manifest: $('#train-manifest').value.trim(),
    eval_manifest: $('#eval-manifest').value.trim() || null, device: $('#train-device').value,
    config: { ...custom, training_arguments: trainingArguments },
  };
  if (!payload.train_manifest) throw new Error('Enter the local path to a training manifest.');
  setBusy(form, true, 'Queueing…');
  try {
    const result = await api('/api/training', { method: 'POST', body: JSON.stringify(payload) });
    state.training.unshift(result.training); state.jobs.unshift(result.job); updateChrome(); render(); toast('Training run added to the queue.', 'success');
  } finally { if (form.isConnected) setBusy(form, false); }
}

async function submitSettings(form) {
  const integerFields = new Set(['output_sample_rate', 'output_channels', 'max_loaded_models', 'max_upload_mb', 'queue_workers', 'auto_unload_minutes', 'port']);
  const values = {};
  for (const [name, raw] of new FormData(form).entries()) {
    values[name] = integerFields.has(name) ? (raw === '' ? null : Number(raw)) : raw;
  }
  if ('output_sample_rate' in values && values.output_sample_rate == null) values.output_sample_rate = null;
  setBusy(form, true, 'Saving…');
  try {
    state.settings = await api('/api/settings', { method: 'PUT', body: JSON.stringify(values) });
    setLocalePreference(state.settings.interface_language || 'system', { translate: false });
    syncDefaultScript();
    applyTheme(state.settings.theme); render(); toast('Settings saved.', 'success');
  } finally { if (form.isConnected) setBusy(form, false); }
}

async function prepareWaveform() {
  const canvas = $('#waveform-canvas'); const stage = $('#waveform-stage'); const asset = currentAsset();
  if (!canvas || !stage || !asset) return;
  if (!state.editor.peaks && state.online && !state.editor.waveformLoading) {
    state.editor.waveformLoading = true;
    try { state.editor.peaks = await api(`/api/assets/${encodeURIComponent(asset.id)}/waveform?buckets=1600`); }
    catch (error) { toast(`Waveform analysis failed: ${error.message}`, 'error'); }
    finally { state.editor.waveformLoading = false; }
  }
  drawWaveform();
  const pointToTime = (event) => {
    const rect = canvas.getBoundingClientRect();
    return clamp((event.clientX - rect.left) / rect.width, 0, 1) * Number(asset.duration || state.editor.peaks?.duration || 0);
  };
  canvas.onpointerdown = (event) => {
    canvas.setPointerCapture(event.pointerId); state.editor.dragging = true;
    state.editor.anchor = pointToTime(event); state.editor.start = state.editor.anchor; state.editor.end = state.editor.anchor; updateSelectionUI();
  };
  canvas.onpointermove = (event) => {
    if (!state.editor.dragging) return;
    const time = pointToTime(event); state.editor.start = Math.min(state.editor.anchor, time); state.editor.end = Math.max(state.editor.anchor, time); updateSelectionUI();
  };
  canvas.onpointerup = (event) => { state.editor.dragging = false; try { canvas.releasePointerCapture(event.pointerId); } catch (_) { /* already released */ } updateSelectionUI(); };
  const audio = $('#editor-audio');
  if (audio) {
    audio.ontimeupdate = () => {
      $('#transport-time') && ($('#transport-time').textContent = `${formatDuration(audio.currentTime)} / ${formatDuration(asset.duration)}`);
      if (audio.dataset.stopAt && audio.currentTime >= Number(audio.dataset.stopAt)) { audio.pause(); delete audio.dataset.stopAt; }
    };
    audio.onended = () => { const button = $('[data-action="play-asset"]'); if (button) button.innerHTML = icon('play'); };
  }
}

function updateSelectionUI() {
  const asset = currentAsset(); if (!asset) return;
  $('#selection-start') && ($('#selection-start').textContent = formatDuration(state.editor.start));
  $('#selection-end') && ($('#selection-end').textContent = formatDuration(state.editor.end));
  $('#selection-length') && ($('#selection-length').textContent = formatDuration(Math.max(0, state.editor.end - state.editor.start)));
  drawWaveform();
}

function drawWaveform() {
  const canvas = $('#waveform-canvas'); const stage = $('#waveform-stage'); const asset = currentAsset();
  if (!canvas || !stage || !asset) return;
  const rect = stage.getBoundingClientRect(); const ratio = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.round(rect.width * ratio)); const height = Math.max(1, Math.round(rect.height * ratio));
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  const ctx = canvas.getContext('2d'); ctx.clearRect(0, 0, width, height);
  const styles = getComputedStyle(document.documentElement);
  const accent = styles.getPropertyValue('--accent').trim() || '#b7f34a';
  const muted = styles.getPropertyValue('--muted').trim() || '#77808c';
  const duration = Number(asset.duration || state.editor.peaks?.duration || 1);
  const selectionStart = clamp(state.editor.start / duration, 0, 1) * width;
  const selectionEnd = clamp((state.editor.end || duration) / duration, 0, 1) * width;
  if (Math.abs(selectionEnd - selectionStart) > 1) { ctx.fillStyle = `${accent}20`; ctx.fillRect(selectionStart, 0, selectionEnd - selectionStart, height); }
  const peaks = state.editor.peaks?.peaks || [];
  if (!peaks.length) {
    ctx.strokeStyle = muted; ctx.globalAlpha = .5; ctx.beginPath(); ctx.moveTo(0, height / 2);
    for (let x = 0; x <= width; x += Math.max(2, ratio * 3)) ctx.lineTo(x, height / 2 + Math.sin(x / 19) * height * .06 * (1 + Math.sin(x / 71)));
    ctx.stroke(); ctx.globalAlpha = 1;
  } else {
    const center = height / 2; const step = width / peaks.length;
    ctx.strokeStyle = accent; ctx.lineWidth = Math.max(1, ratio); ctx.globalAlpha = .82; ctx.beginPath();
    peaks.forEach(([minimum, maximum], index) => { const x = index * step; ctx.moveTo(x, center + minimum * center * .88); ctx.lineTo(x, center + maximum * center * .88); }); ctx.stroke(); ctx.globalAlpha = 1;
  }
  if (Math.abs(selectionEnd - selectionStart) > 1) {
    ctx.strokeStyle = accent; ctx.lineWidth = ratio; [selectionStart, selectionEnd].forEach((x) => { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke(); });
  }
}

function applyTheme(preference) {
  const theme = preference === 'system'
    ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark')
    : (preference || 'dark');
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('voicehub-studio-theme', preference || theme);
  const toggle = $('#theme-toggle [data-icon]');
  if (toggle) { toggle.dataset.icon = theme === 'dark' ? 'sun' : 'moon'; hydrateIcons($('#theme-toggle')); }
}

function connectEvents() {
  if (!state.online || typeof EventSource === 'undefined') return;
  const stream = new EventSource('/api/events');
  const names = ['job.created', 'job.updated', 'generation.created', 'generation.updated', 'generation.deleted', 'voice.created', 'voice.updated', 'voice.deleted', 'asset.created', 'asset.deleted', 'training.created', 'training.updated', 'runtime.unloaded', 'settings.updated'];
  const schedule = () => {
    clearTimeout(state.refreshTimer);
    state.refreshTimer = setTimeout(refreshCollections, 350);
  };
  names.forEach((name) => stream.addEventListener(name, schedule));
  stream.onerror = () => {
    stream.close();
    setTimeout(() => { if (state.online) connectEvents(); }, 4000);
  };
  state.eventStream = stream;
}

window.addEventListener('hashchange', () => {
  const route = location.hash.slice(1);
  state.route = route in ROUTES ? route : 'generate';
  render();
});

window.addEventListener('resize', () => { if (state.route === 'editor') drawWaveform(); });

$('#command-trigger')?.addEventListener('click', () => showCommandPalette());
$('#hardware-pill')?.addEventListener('click', () => { state.settingsTab = 'compute'; navigate('settings'); });
$('#theme-toggle')?.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next); state.settings.theme = next;
  if (state.online) api('/api/settings', { method: 'PUT', body: JSON.stringify({ theme: next }) }).catch(() => {});
  if (state.route === 'editor') drawWaveform();
});
$('#language-toggle')?.addEventListener('click', async () => {
  const next = getLocale() === 'tr' ? 'en' : 'tr';
  state.settings.interface_language = next;
  setLocalePreference(next, { translate: false });
  syncDefaultScript();
  render();
  if (state.online) {
    try {
      state.settings = await api('/api/settings', { method: 'PUT', body: JSON.stringify({ interface_language: next }) });
    } catch (error) {
      toast(error.message, 'error');
    }
  }
});
$('#mobile-menu')?.addEventListener('click', () => document.body.classList.toggle('nav-open'));
$('#mobile-scrim')?.addEventListener('click', closeMobileNav);
$('#modal-layer')?.addEventListener('click', (event) => { if (event.target.id === 'modal-layer') closeModal(); });

document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); showCommandPalette(); return; }
  if (event.key === 'Escape' && $('#modal-layer')?.classList.contains('open')) { closeModal(); return; }
  const input = $('#command-input'); if (!input) return;
  const items = $$('.command-item', $('#command-results'));
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault(); commandIndex = (commandIndex + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
    items.forEach((item, index) => item.classList.toggle('active', index === commandIndex)); items[commandIndex]?.scrollIntoView({ block: 'nearest' });
  } else if (event.key === 'Enter' && items[commandIndex]) { event.preventDefault(); items[commandIndex].click(); }
});

matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
  if ((state.settings.theme || localStorage.getItem('voicehub-studio-theme')) === 'system') applyTheme('system');
});

hydrateIcons();
setLocalePreference(getLocalePreference(), { translate: false });
localizeTree(document);
applyTheme(localStorage.getItem('voicehub-studio-theme') || 'dark');
if (!location.hash) history.replaceState(null, '', '#generate');
loadWorkspace().then(() => {
  applyTheme(state.settings.theme || localStorage.getItem('voicehub-studio-theme') || 'dark');
  connectEvents();
  setInterval(() => {
    if (document.visibilityState === 'visible' && state.jobs.some((job) => ['queued', 'running'].includes(job.status))) refreshCollections();
  }, 4000);
});
