from __future__ import annotations

from pathlib import Path

from voicehub_studio.schemas import VoiceCreate
from voicehub_studio.services.audio import concatenate_audio, process_audio
from voicehub_studio.services.model_catalog import ModelCatalogService
from voicehub_studio.services.runtime import (
    _install_voicehub_compatibility,
    apply_voice_conditioning,
)


def test_catalog_contains_full_tts_registry() -> None:
    catalog = ModelCatalogService()
    models = catalog.list_models()
    assert len(models) >= 34
    assert {"qwen3tts", "chatterbox", "f5tts", "xtts", "kokoro"}.issubset(
        {model["model_type"] for model in models}
    )
    by_type = {model["model_type"]: model for model in models}
    assert by_type["supertonic"]["supports_turkish"] is True
    assert by_type["supertonic"]["turkish"]["language"] == "tr"
    assert by_type["vits"]["turkish"]["checkpoint"] == "facebook/mms-tts-tur"
    assert by_type["qwen3tts"]["supports_turkish"] is False


def test_turkish_language_suggestions_follow_adapter_codes() -> None:
    catalog = ModelCatalogService()
    supertonic = catalog.generation_schema("supertonic")
    language = next(
        field for field in supertonic["conditioning"] if field["name"] == "language"
    )
    assert language["suggestions"][0] == "tr"


def test_clone_profile_maps_to_supported_adapter_names() -> None:
    schema = {
        "conditioning": [
            {"name": "reference_audio", "control": "asset"},
            {"name": "prompt_text", "control": "textarea"},
            {"name": "language", "control": "text"},
            {"name": "mode", "control": "select"},
        ]
    }
    voice = {
        "kind": "clone",
        "reference_path": "/tmp/reference.wav",
        "reference_text": "Reference words",
        "language": "English",
        "conditioning": {},
    }
    result = apply_voice_conditioning(schema, voice, {"language": "Turkish"})
    assert result["reference_audio"] == "/tmp/reference.wav"
    assert result["prompt_text"] == "Reference words"
    assert result["mode"] == "voice_clone"
    assert result["language"] == "Turkish"


def test_design_and_preset_contracts() -> None:
    design = VoiceCreate(
        name="Documentary", kind="design", design_prompt="A grounded narrator"
    )
    preset = VoiceCreate(name="Vivian", kind="preset", speaker="Vivian")
    assert design.kind == "design"
    assert preset.speaker == "Vivian"


def test_qwen_public_generation_input_bridge_preserves_conditioning() -> None:
    class FakeQwenModel:
        def prepare_inputs_for_generation(self, text: str, **kwargs):
            raise AssertionError("The incompatible inherited path was used")

    model = FakeQwenModel()
    _install_voicehub_compatibility("qwen3tts", model)

    result = model.prepare_inputs_for_generation(
        "Hello",
        mode="custom_voice",
        speaker="Vivian",
        language="English",
    )

    assert result == {
        "text": "Hello",
        "mode": "custom_voice",
        "speaker": "Vivian",
        "language": "English",
    }

    _install_voicehub_compatibility("qwen3tts", model)
    assert model.prepare_inputs_for_generation("Again") == {"text": "Again"}


def test_every_audio_operation_and_concat_path(tone_file: Path, tmp_path: Path) -> None:
    cases = {
        "trim": [{"op": "trim", "start": 0.1, "end": 1.0}],
        "keep_ranges": [
            {
                "op": "keep_ranges",
                "ranges": [{"start": 0.1, "end": 0.4}, {"start": 0.8, "end": 1.1}],
            }
        ],
        "remove_range": [{"op": "remove_range", "start": 0.4, "end": 0.8}],
        "gain": [{"op": "gain", "db": -4}],
        "normalize": [{"op": "normalize", "target_lufs": -16}],
        "fade_in": [{"op": "fade_in", "duration": 0.15}],
        "fade_out": [{"op": "fade_out", "duration": 0.15}],
        "denoise": [{"op": "denoise", "strength": 8}],
        "speed": [{"op": "speed", "factor": 1.25}],
        "pitch": [{"op": "pitch", "semitones": 2}],
        "reverse": [{"op": "reverse"}],
        "trim_silence": [
            {"op": "trim_silence", "threshold_db": -42, "minimum_seconds": 0.1}
        ],
        "highpass": [{"op": "highpass", "frequency": 100}],
        "lowpass": [{"op": "lowpass", "frequency": 10_000}],
        "compress": [{"op": "compress", "threshold_db": -18, "ratio": 2}],
    }
    for name, operations in cases.items():
        details = process_audio(
            tone_file,
            tmp_path / f"{name}.wav",
            operations,
            output_format="wav",
            sample_rate=22_050,
            channels=1,
        )
        assert details["duration"] > 0, name

    plain = concatenate_audio(
        [tone_file, tone_file], tmp_path / "concat.wav", output_format="wav"
    )
    faded = concatenate_audio(
        [tone_file, tone_file],
        tmp_path / "crossfade.wav",
        output_format="wav",
        crossfade=0.1,
    )
    assert plain["duration"] > faded["duration"] > 0
