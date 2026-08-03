# Architecture

## Process boundary

```text
Linux window / browser
        │ HTTP + server-sent events
        ▼
FastAPI application
 ├─ model catalog and dynamic setting schemas
 ├─ persistent SQLite job queue
 ├─ voice / asset / generation library
 ├─ FFmpeg non-destructive editor
 └─ VoiceHub runtime and training services
        │
        ├─ CPU
        └─ CUDA / MPS / XPU
```

The frontend never imports a model implementation. It asks `/api/models/{model_type}` for a schema generated from the installed VoiceHub adapter. Fields are grouped by their destination:

- `generation_config` becomes `voicehub.TTSGenerationConfig`.
- `model_kwargs` is passed to `model.generate(...)`.
- `model_config` is passed while constructing the lazy model.
- `optimization` becomes `voicehub.TTSOptimizationConfig`.

This keeps the application compatible when VoiceHub adds parameters or adapters. Explicit inputs make common controls pleasant; JSON object overrides retain complete access.

## Localization and language routing

The interface ships English and Turkish strings in a standalone browser module. The selected UI language is persisted in the same XDG settings file and can follow the Linux locale. Localization never changes user text, checkpoint paths, JSON, or adapter values.

Speech language and interface language are independent. A small compatibility map records only verified Turkish workflows and the exact adapter value they expect: `tr` for Supertonic, XTTS, and Zonos, or the dedicated `facebook/mms-tts-tur` checkpoint for VITS. The global Turkish default is applied only to models that advertise Turkish support, preventing invalid language values from leaking into Qwen or another incompatible adapter.

## Model lifecycle

`VoiceHubRuntimeManager` keys a runtime by model type, checkpoint, resolved device, loading configuration, and optimization configuration. It lazily builds `AutoModelForTextToSpeech`, loads weights only in a worker, keeps a bounded least-recently-used cache, and releases CUDA memory on eviction. The default one-worker queue prevents two large jobs from unexpectedly competing for one GPU.

CPU is always a valid target. `auto` chooses CUDA, MPS, XPU, then CPU according to the installed PyTorch runtime. Detection from `nvidia-smi` is shown separately from PyTorch availability so a driver-only installation is not falsely reported as inference-ready.

## Voice profiles

A voice profile stores conditioning, not a model copy:

- Clone/recording: authorized reference asset, transcript, and optional adapter-specific values.
- Design: a natural-language voice description.
- Preset: the exact speaker identifier expected by a checkpoint.

At generation time, `apply_voice_conditioning` maps the profile to names actually supported by the selected adapter (`speaker_audio_path`, `reference_audio`, `prompt_wav_path`, and similar variants). Explicit per-generation values win over profile defaults.

## Audio editing

Assets are immutable in normal workflows. Every render receives an ordered operation list, runs one validated FFmpeg graph, writes a new file, then records its parent and operation history. Complex range operations are composed before simple filters. Waveforms use downsampled mono float samples and are drawn by the browser canvas; original audio is never sent elsewhere.

## Training

Studio does not invent a universal dataset format. A training job asks the selected VoiceHub model for its training adapter and dataset contract, validates local manifests, frees inference VRAM, constructs VoiceHub `Trainer` and `TrainingArguments`, reports steps through the same event stream, and saves a final portable artifact. A one-step smoke test is the safe default.

## Extension points

- Add a TTS model in VoiceHub; it appears in the registry automatically.
- Add friendly labels or bounds for a parameter in `services/model_catalog.py`; unknown fields still receive inferred controls.
- Add an audio operation in `services/audio.py`, then add an effect tile in `static/app.js`.
- Add job types by registering a handler on `JobQueue` during `ApplicationState` initialization.
- Build a multi-track timeline on the existing `projects`, `tracks`, and `clips` tables without changing stored assets.
