# Repository research and decisions

Research was performed against upstream repositories and documentation on 2026-08-03. No code was copied from the comparison applications.

## VoiceHub

[kadirnar/voicehub](https://github.com/kadirnar/voicehub) is the model foundation. Version 0.3.0 exposes a unified `AutoModelForTextToSpeech`, `TTSGenerationConfig`, normalized output, lazy loading, optimization policies, and training contracts. Its current registry contains 34 TTS models and keeps model implementations inside the package rather than making the application maintain a second adapter layer. Studio pins commit `566db6822d47a335c720efb9ea66d7bcb22a1a82` (2026-08-02) because the PyPI package was behind the documented 0.3.0 repository state during testing.

That pinned revision's generic public generation path passes Qwen text into a keyword-only processor and loses Qwen's raw conditioning arguments. Studio installs a narrowly scoped `qwen3tts` input bridge before loading the model. It preserves VoiceHub's public `model.generate(...)` lifecycle and was verified with the real 0.6B CustomVoice checkpoint on CUDA; the bridge can be removed when the upstream adapter owns its input preparation.

The [capability matrix](https://kadirnar.github.io/voicehub/models/tts-capabilities/) matters more than a fixed list of buttons: cloning, voice design, style prompting, dialogue, multilingual support, and fine-tuning vary by model. Studio therefore reads the registry and introspects adapter signatures instead of pretending every control works everywhere.

The [inference guide](https://kadirnar.github.io/voicehub/guides/inference/) informed the normalized generation path. The [optimization guide](https://kadirnar.github.io/voicehub/guides/tts-optimization/) informed separate device, precision, attention, kernel, compile, and model-cache controls. The [installation guide](https://kadirnar.github.io/voicehub/getting-started/installation/) establishes Python 3.10–3.12 and PyTorch 2.8 as the supported baseline.

## Qwen3-TTS

[QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) provides three distinct workflows: custom preset voices, voice design from natural-language instructions, and voice cloning from reference audio/transcript (with an optional embedding-only mode). Studio models these as separate creation modes while still showing the adapter's exact advanced values.

## Turkish language support

[Supertonic 3](https://huggingface.co/Supertone/supertonic-3) explicitly publishes Turkish under the `tr` language code, runs locally on CPU or GPU, and has a compact on-device-oriented runtime. Studio uses it as the recommended one-click Turkish default through VoiceHub. The checkpoint is OpenRAIL-M licensed.

[Meta MMS Turkish TTS](https://huggingface.co/facebook/mms-tts-tur) is a dedicated Turkish VITS checkpoint using the ISO 639-3 code `tur`. Studio exposes it as a compact alternative through VoiceHub's VITS adapter and surfaces its CC-BY-NC-4.0 limitation. The installed VoiceHub XTTS and Zonos adapters also declare `tr` in their native language tables, so Studio marks those as Turkish-capable cloning or expressive workflows without sending Turkish arguments to unsupported adapters.

## Product references

- [Voicebox](https://github.com/jamiepine/voicebox) demonstrates the value of a local-first engine abstraction, presets, post-effects, long-text work, and a timeline-oriented desktop experience. Its broad Linux compute targets reinforced keeping device selection explicit.
- [OmniVoice Studio](https://github.com/debpalash/OmniVoice-Studio) demonstrates a productive clone/design/dubbing workflow and queue-based local backend. Its source-available license is not used as a code dependency.
- [Chatterbox](https://github.com/resemble-ai/chatterbox), [Coqui TTS](https://github.com/coqui-ai/TTS), and [F5-TTS](https://github.com/SWivid/F5-TTS) were reviewed for reference-audio and expressive-generation conventions. Studio accesses these families through VoiceHub rather than creating direct integrations.

## Resulting design choices

1. **Local service plus desktop shell.** Python and GPU libraries remain in their natural ecosystem; the interface can evolve independently and can be automated through the same API.
2. **Dynamic controls plus JSON.** Friendly common settings are not allowed to hide adapter-specific functionality.
3. **Persistent, serial queue by default.** Model downloads and inference remain responsive while protecting a single GPU from accidental overcommit.
4. **Non-destructive assets.** Cutting or processing produces a derived file with an auditable operation list.
5. **Consent is data.** Saving a cloned or recorded voice requires an explicit authorization flag and can retain a local note.
6. **Training stays model-owned.** Dataset and objective assumptions come from VoiceHub's training contracts, not a misleading universal form.
