# VoiceHub Studio

VoiceHub Studio is a local-first Linux application for text-to-speech, voice cloning, voice design, reusable voice profiles, waveform editing, model loading, and fine-tuning. It uses [kadirnar/voicehub](https://github.com/kadirnar/voicehub) as its model layer instead of binding the interface to one TTS engine.

English documentation | [Türkçe belge](README.tr.md)

The application is deliberately split into a Python service and a responsive desktop interface. The same build can open in a native `pywebview` window, a normal browser, or headless server mode.

## What is implemented

- All 34 VoiceHub TTS adapters are discovered at runtime, with an offline catalog fallback.
- Each adapter's real `_generate` and configuration signatures become model-specific controls automatically.
- A raw JSON escape hatch exposes new or unusual model, generation, and loading values without waiting for a UI release.
- CPU, CUDA, CUDA device index, MPS, and Intel XPU routing, with automatic device selection and precision controls.
- Lazy model loading, bounded LRU runtime cache, explicit unload, idle unload, and a serial-by-default GPU-safe queue.
- Text-to-speech, preset speakers, direct reference-audio cloning, natural-language voice design, style instructions, seeds, sampling, language, output format/rate/channels, and loudness normalization.
- Saved clone, recording, design, and preset voice profiles. Clone profiles require a local authorization confirmation.
- Microphone capture and audio upload for reference voices.
- Non-destructive audio cutting and effects: trim/keep, delete a range, silence-based auto-cut, gain, normalization, denoise, speed, pitch, fades, silence trimming, compression, reverse, high-pass, and low-pass.
- Audio concatenation with optional crossfade.
- Persistent generations, assets, voices, projects, jobs, and training runs in SQLite.
- VoiceHub-native fine-tuning contracts, datasets, `TrainingArguments`, progress callbacks, and portable model artifacts.
- Local REST API, OpenAPI docs, server-sent job events, dark/light themes, command palette, and responsive Linux UI.
- Complete English and Turkish interface localization with a one-click Turkish speech setup.

## Requirements

- Linux on x86-64 or another PyTorch-supported architecture
- Python 3.10–3.12 (3.12 recommended)
- FFmpeg and FFprobe
- 16 GB RAM minimum; more is useful for larger checkpoints
- Optional NVIDIA GPU with a PyTorch 2.8-compatible CUDA build

Model downloads can be large. Each checkpoint also has its own upstream license and hardware requirements; inspect those before using it commercially.

## Quick start

The bootstrap script installs `uv` locally when necessary, creates `.venv`, installs a PyTorch 2.8 CPU or CUDA 12.8 build, and installs Studio. The project pins VoiceHub 0.3.0 to the researched upstream Git commit because the package currently published under that name on PyPI is older.

```bash
git clone https://github.com/kadirnar/voicehub-studio.git
cd voicehub-studio
./scripts/bootstrap.sh --cuda
./scripts/run.sh
```

For a complete current-user Linux application installation—including the native window dependency, desktop menu entry, icon, and launcher—run:

```bash
./scripts/install-linux.sh --cuda --system-deps
```

Use `--cpu` instead of `--cuda` on a machine without an NVIDIA GPU. The installer can also accept `--training` and `--launch`. It never starts a privileged background service; inference remains local to the signed-in user.

For CPU-only operation:

```bash
./scripts/bootstrap.sh --cpu
./scripts/run.sh --browser
```

Add fine-tuning dependencies with `--training`, and the optional native Qt webview dependencies with `--desktop`:

```bash
./scripts/bootstrap.sh --cuda --training --desktop
```

If `pywebview` is not installed or its Qt/XCB system libraries are unavailable, `./scripts/run.sh` opens the normal browser automatically. Server-only mode is available with:

```bash
./scripts/run.sh --server --host 127.0.0.1 --port 8765
```

Then open <http://127.0.0.1:8765>. Interactive API documentation is at <http://127.0.0.1:8765/api/docs>.

After bootstrapping with `--desktop`, add a launcher to the current Linux user's application menu:

```bash
./scripts/install-desktop.sh
```

Remove only the launcher while preserving all local data with `./scripts/uninstall-linux.sh`. Add `--purge-data` only when you also intend to permanently delete local voices, generations, settings, and caches.

## Manual installation

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python "torch>=2.8,<2.9" \
  --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .venv/bin/python -e ".[test]"
.venv/bin/voicehub-studio --browser
```

Use `https://download.pytorch.org/whl/cpu` for a CPU-only PyTorch build.

## First generation

1. Open **Model library**, choose a model, and click **Use**. Qwen3-TTS is the default because one family supports presets, cloning, design, multilingual speech, and expressive instructions. Its modes require different official checkpoints, so Studio switches compatible CustomVoice, Base, and VoiceDesign variants when you change modes; a custom local path remains untouched.
2. On **Generate**, choose Speak, Clone, or Design. The available modes follow the selected adapter's capabilities.
3. Enter the checkpoint. Hugging Face checkpoints download on first load; local checkpoint directories work too.
4. Open **Every model setting** for adapter-specific controls, per-render compute/output options, and JSON overrides.
5. Generate. The job continues if you navigate elsewhere in the interface.

To save a reference voice, use **Voices → Add voice → Clone** or **Record**. The app intentionally asks you to confirm speaker authorization before the profile can be stored.

## Turkish support

Use the **TR** button in the top bar to switch the full interface to Turkish. The selection is saved in the XDG configuration and can also follow the Linux system language.

On **Generate**, click **Turkish setup / Türkçe kurulumu**. Studio selects `Supertone/supertonic-3`, sets its model-native language code to `tr`, supplies a Turkish starter script, and saves those generation defaults. The model supports CPU and GPU execution. The model library also marks additional Turkish workflows:

- `facebook/mms-tts-tur` through the VITS adapter for compact Turkish synthesis. This checkpoint is CC-BY-NC-4.0.
- XTTS v2 with language code `tr` for authorized cross-language voice cloning.
- Zonos with language code `tr` for expressive synthesis or cloning.

Model language support and licenses are checkpoint-specific. Studio deliberately does not send `tr` to adapters that do not advertise Turkish support.

## Data locations

Studio follows XDG directories by default:

- Data and SQLite: `~/.local/share/voicehub-studio`
- Settings: `~/.config/voicehub-studio/settings.json`
- Cache: `~/.cache/voicehub-studio`

For development or a portable workspace, set `VOICEHUB_STUDIO_HOME` to put all mutable state below one directory:

```bash
VOICEHUB_STUDIO_HOME="$PWD/voicehub-studio-data" ./scripts/run.sh --browser
```

The service refuses non-loopback binds unless `VOICEHUB_STUDIO_ALLOW_REMOTE=1` is set. This is intentional: the local API does not include remote authentication.

## Development and tests

```bash
./scripts/bootstrap.sh --cpu
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m compileall -q voicehub_studio
git diff --check
```

The test suite exercises persistence, request validation, model discovery, voice conditioning, uploads, waveform extraction, FFmpeg effects, queue completion, and API behavior without downloading a checkpoint.

See [Architecture](docs/architecture.md) for extension points and [Research notes](docs/research.md) for the repository survey and design rationale.

## License

VoiceHub Studio source is Apache-2.0. VoiceHub is also Apache-2.0, but checkpoint weights and datasets retain their own licenses.
