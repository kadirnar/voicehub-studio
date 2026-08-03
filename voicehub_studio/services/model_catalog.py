"""VoiceHub-backed model discovery and dynamic settings schemas."""

from __future__ import annotations

import importlib
import inspect
import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from types import UnionType
from typing import Any, get_args, get_origin

DISPLAY_NAMES = {
    "orpheustts": "Orpheus TTS",
    "dia": "Dia",
    "vui": "Vui",
    "chatterbox": "Chatterbox",
    "kokoro": "Kokoro",
    "echo": "Echo TTS",
    "conversationtts": "Conversation TTS",
    "llasa": "Llasa",
    "cosyvoice": "CosyVoice",
    "f5tts": "F5-TTS",
    "gptsovits": "GPT-SoVITS",
    "melotts": "MeloTTS",
    "openvoice": "OpenVoice",
    "outetts": "OuteTTS",
    "parlertts": "Parler-TTS",
    "styletts2": "StyleTTS 2",
    "mosstts": "MOSS-TTS",
    "qwen3tts": "Qwen3-TTS",
    "irodoritts": "Irodori TTS",
    "zonos": "Zonos",
    "zonos2": "Zonos 2",
    "voxcpm": "VoxCPM 2",
    "omnivoice": "OmniVoice",
    "higgstts": "Higgs Audio",
    "xtts": "XTTS v2",
    "vibevoice": "VibeVoice",
    "fishtts": "Fish Speech",
    "csm": "CSM",
    "neutts": "NeuTTS",
    "supertonic": "Supertonic",
    "inflecttts": "Inflect TTS",
    "bark": "Bark",
    "speecht5": "SpeechT5",
    "vits": "VITS / MMS",
}

TURKISH_SUPPORT: dict[str, dict[str, Any]] = {
    "supertonic": {
        "checkpoint": "Supertone/supertonic-3",
        "language": "tr",
        "workflow": "synthesis",
        "recommended": True,
        "license": "OpenRAIL-M",
    },
    "vits": {
        "checkpoint": "facebook/mms-tts-tur",
        "language": None,
        "workflow": "synthesis",
        "recommended": False,
        "license": "CC-BY-NC-4.0",
    },
    "xtts": {
        "checkpoint": "coqui/XTTS-v2",
        "language": "tr",
        "workflow": "voice-cloning",
        "requires_reference": True,
        "recommended": False,
    },
    "zonos": {
        "checkpoint": "Zyphra/Zonos-v0.1-transformer",
        "language": "tr",
        "workflow": "synthesis-or-cloning",
        "recommended": False,
    },
}

LANGUAGE_SUGGESTIONS: dict[str, list[str]] = {
    "supertonic": ["tr", "en"],
    "xtts": ["tr", "en", "de", "fr", "es", "it", "pt", "pl", "ru"],
    "zonos": ["tr", "en-us", "de", "fr", "es", "it", "ja", "zh"],
}

FIELD_PRESENTATION: dict[str, dict[str, Any]] = {
    "mode": {
        "label": "Generation mode",
        "control": "select",
        "choices": ["auto", "custom_voice", "voice_design", "voice_clone"],
        "group": "conditioning",
    },
    "language": {"label": "Language", "control": "text", "group": "conditioning"},
    "speaker": {"label": "Preset speaker", "control": "text", "group": "conditioning"},
    "voice": {"label": "Voice", "control": "text", "group": "conditioning"},
    "speaker_audio_path": {
        "label": "Reference audio",
        "control": "asset",
        "group": "conditioning",
    },
    "reference_audio_path": {
        "label": "Reference audio",
        "control": "asset",
        "group": "conditioning",
    },
    "reference_audio": {
        "label": "Reference audio",
        "control": "asset",
        "group": "conditioning",
    },
    "audio_prompt_path": {
        "label": "Reference audio",
        "control": "asset",
        "group": "conditioning",
    },
    "prompt_wav_path": {
        "label": "Prompt audio",
        "control": "asset",
        "group": "conditioning",
    },
    "reference_text": {
        "label": "Reference transcript",
        "control": "textarea",
        "group": "conditioning",
    },
    "prompt_text": {
        "label": "Prompt transcript",
        "control": "textarea",
        "group": "conditioning",
    },
    "description": {
        "label": "Voice description",
        "control": "textarea",
        "group": "expression",
    },
    "instruct": {
        "label": "Delivery / voice instruction",
        "control": "textarea",
        "group": "expression",
    },
    "instruction": {
        "label": "Delivery instruction",
        "control": "textarea",
        "group": "expression",
    },
    "emotion": {"label": "Emotion", "control": "text", "group": "expression"},
    "exaggeration": {
        "label": "Exaggeration",
        "control": "range",
        "min": 0,
        "max": 2,
        "step": 0.05,
        "group": "expression",
    },
    "cfg_weight": {
        "label": "CFG weight",
        "control": "range",
        "min": 0,
        "max": 2,
        "step": 0.05,
        "group": "sampling",
    },
    "guidance_scale": {
        "label": "Guidance scale",
        "control": "number",
        "min": 0,
        "step": 0.1,
        "group": "sampling",
    },
    "seed": {"label": "Seed", "control": "number", "step": 1, "group": "sampling"},
    "speed": {
        "label": "Speed",
        "control": "range",
        "min": 0.25,
        "max": 3,
        "step": 0.05,
        "group": "sampling",
    },
    "temperature": {
        "label": "Temperature",
        "control": "range",
        "min": 0,
        "max": 2,
        "step": 0.01,
        "group": "sampling",
    },
    "top_p": {
        "label": "Top P",
        "control": "range",
        "min": 0,
        "max": 1,
        "step": 0.01,
        "group": "sampling",
    },
    "top_k": {
        "label": "Top K",
        "control": "number",
        "min": 0,
        "step": 1,
        "group": "sampling",
    },
    "max_new_tokens": {
        "label": "Maximum new tokens",
        "control": "number",
        "min": 1,
        "step": 1,
        "group": "sampling",
    },
    "repetition_penalty": {
        "label": "Repetition penalty",
        "control": "number",
        "min": 0,
        "step": 0.01,
        "group": "sampling",
    },
    "x_vector_only_mode": {
        "label": "Speaker embedding only",
        "control": "switch",
        "group": "conditioning",
    },
    "do_sample": {"label": "Sampling", "control": "switch", "group": "sampling"},
    "non_streaming_mode": {
        "label": "Non-streaming mode",
        "control": "switch",
        "group": "runtime",
    },
}

COMMON_GENERATION_FIELDS = (
    ("seed", None),
    ("speed", None),
    ("temperature", None),
    ("top_p", None),
    ("max_new_tokens", None),
)


def _fallback_catalog() -> dict[str, Any]:
    resource = resources.files("voicehub_studio.resources").joinpath(
        "model_catalog.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))


def _serializable(value: Any) -> Any:
    if value is inspect.Parameter.empty or value is inspect.Signature.empty:
        return None
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_serializable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serializable(item) for key, item in value.items()}
    return str(value)


def _annotation_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "any"
    if isinstance(annotation, str):
        return annotation
    origin = get_origin(annotation)
    if origin in {list, tuple, dict, set}:
        arguments = ", ".join(_annotation_name(item) for item in get_args(annotation))
        return f"{origin.__name__}[{arguments}]"
    if origin is UnionType or origin is __import__("typing").Union:
        return " | ".join(_annotation_name(item) for item in get_args(annotation))
    return getattr(annotation, "__name__", str(annotation).replace("typing.", ""))


def _infer_control(name: str, annotation: Any, default: Any) -> str:
    if name in FIELD_PRESENTATION:
        return FIELD_PRESENTATION[name]["control"]
    type_name = _annotation_name(annotation).lower()
    if isinstance(default, bool) or "bool" in type_name:
        return "switch"
    if isinstance(default, (int, float)) or "int" in type_name or "float" in type_name:
        return "number"
    if any(word in name for word in ("text", "prompt", "description", "instruction")):
        return "textarea"
    if any(word in name for word in ("path", "audio", "wav")):
        return "asset"
    return "text"


def _field_schema(
    name: str, parameter: inspect.Parameter | None, *, source: str
) -> dict[str, Any]:
    default = (
        None
        if parameter is None or parameter.default is inspect.Parameter.empty
        else parameter.default
    )
    annotation = inspect.Parameter.empty if parameter is None else parameter.annotation
    presentation = FIELD_PRESENTATION.get(name, {})
    schema = {
        "name": name,
        "label": presentation.get("label", name.replace("_", " ").title()),
        "source": source,
        "type": _annotation_name(annotation),
        "control": _infer_control(name, annotation, default),
        "group": presentation.get("group", "advanced"),
        "required": bool(
            parameter is not None and parameter.default is inspect.Parameter.empty
        ),
        "default": _serializable(default),
    }
    for key in ("choices", "min", "max", "step", "help"):
        if key in presentation:
            schema[key] = presentation[key]
    return schema


def _training_support(model_type: str) -> dict[str, Any]:
    try:
        from voicehub import get_training_spec, get_tts_dataset_spec

        training = get_training_spec(model_type)
        dataset = get_tts_dataset_spec(model_type)
        return {
            "support": getattr(
                getattr(training, "support", None),
                "value",
                str(getattr(training, "support", "unknown")),
            ),
            "family": getattr(training, "family_name", None),
            "training_checkpoint": getattr(training, "training_checkpoint", None),
            "dataset_readiness": getattr(
                getattr(dataset, "readiness", None),
                "value",
                str(getattr(dataset, "readiness", "unknown")),
            ),
            "sample_rate": getattr(dataset, "sample_rate", None),
        }
    except Exception as error:
        return {"support": "unknown", "error": str(error)}


class ModelCatalogService:
    """Discovers VoiceHub models without loading any checkpoint."""

    def __init__(self) -> None:
        self._fallback = _fallback_catalog()

    @property
    def voicehub_available(self) -> bool:
        try:
            import voicehub  # noqa: F401

            return True
        except Exception:
            return False

    @property
    def voicehub_version(self) -> str | None:
        try:
            import voicehub

            return voicehub.__version__
        except Exception:
            return self._fallback.get("voicehub_version")

    @lru_cache(maxsize=1)
    def list_models(self) -> list[dict[str, Any]]:
        try:
            from voicehub import AutoModelForTextToSpeech

            models = []
            for spec in AutoModelForTextToSpeech.available_models():
                capabilities = list(spec.capabilities)
                models.append(
                    self._enrich(
                        {
                            "model_type": spec.model_type,
                            "default_checkpoint": spec.default_model_path,
                            "architecture": spec.architecture,
                            "components": list(spec.components),
                            "capabilities": capabilities,
                            "install_extra": spec.install_extra,
                            "native": spec.is_voicehub_native,
                        }
                    )
                )
            return models
        except Exception:
            return [
                self._enrich(dict(model), installed=False)
                for model in self._fallback["models"]
            ]

    def _enrich(
        self, model: dict[str, Any], *, installed: bool = True
    ) -> dict[str, Any]:
        capabilities = set(model.get("capabilities", []))
        model_type = model["model_type"]
        model.update(
            {
                "display_name": DISPLAY_NAMES.get(
                    model_type, model_type.replace("_", " ").title()
                ),
                "installed": installed,
                "can_clone": "voice-cloning" in capabilities
                or "speaker-embedding" in capabilities,
                "can_design": "voice-design" in capabilities
                or "prompted-style" in capabilities,
                "can_style": bool(
                    capabilities.intersection(
                        {"expressive-speech", "prompted-style", "emotion"}
                    )
                ),
                "can_train": "fine-tuning" in capabilities,
                "license_warning": "noncommercial" in capabilities,
                "supports_turkish": model_type in TURKISH_SUPPORT,
                "turkish": TURKISH_SUPPORT.get(model_type),
                "docs_url": f"https://kadirnar.github.io/voicehub/models/providers/{model_type}/",
            }
        )
        return model

    def get_model(self, model_type: str) -> dict[str, Any]:
        normalized = model_type.strip().lower()
        for model in self.list_models():
            if model["model_type"] == normalized:
                return model
        raise KeyError(f"Unknown VoiceHub TTS model: {model_type}")

    @lru_cache(maxsize=64)
    def generation_schema(self, model_type: str) -> dict[str, Any]:
        model = self.get_model(model_type)
        generation_fields = {
            name: _field_schema(name, None, source="generation_config")
            for name, _ in COMMON_GENERATION_FIELDS
        }
        model_fields: dict[str, dict[str, Any]] = {}
        config_fields: dict[str, dict[str, Any]] = {}
        error: str | None = None
        try:
            from voicehub import get_model_spec

            spec = get_model_spec(model_type)
            module = importlib.import_module(spec.module)
            model_class = getattr(module, spec.class_name)
            signature = inspect.signature(model_class._generate)
            for name, parameter in signature.parameters.items():
                if name in {"self", "text", "output_file", "seed"}:
                    continue
                if parameter.kind in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }:
                    continue
                model_fields[name] = _field_schema(
                    name, parameter, source="model_kwargs"
                )

            passthrough: set[str] = set()
            for attribute_name in (
                "passthrough_generation_options",
                "_GENERATION_OPTIONS",
                "GENERATION_OPTIONS",
            ):
                values = getattr(model_class, attribute_name, None)
                if values:
                    passthrough.update(str(value) for value in values)
            for name in sorted(passthrough):
                if name not in generation_fields and name not in model_fields:
                    model_fields[name] = _field_schema(
                        name, None, source="model_kwargs"
                    )

            config_module = importlib.import_module(spec.config_module)
            config_class = getattr(config_module, spec.config_class)
            config_signature = inspect.signature(config_class.__init__)
            for name, parameter in config_signature.parameters.items():
                if name in {"self", "kwargs", "name_or_path", "sample_rate"}:
                    continue
                if parameter.kind in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }:
                    continue
                config_fields[name] = _field_schema(
                    name, parameter, source="model_config"
                )
        except Exception as exception:
            error = str(exception)

        if model_type == "qwen3tts" and "mode" in model_fields:
            model_fields["mode"]["choices"] = [
                "auto",
                "custom_voice",
                "voice_design",
                "voice_clone",
            ]
        if model_type in LANGUAGE_SUGGESTIONS and "language" in model_fields:
            model_fields["language"]["suggestions"] = LANGUAGE_SUGGESTIONS[model_type]
        return {
            "model": model,
            "generation": list(generation_fields.values()),
            "conditioning": list(model_fields.values()),
            "model_config": list(config_fields.values()),
            "training": _training_support(model_type),
            "introspection_error": error,
            "advanced_json": True,
        }
