"""VoiceHub model lifecycle, conditioning, and generation jobs."""

from __future__ import annotations

import gc
import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from types import MethodType
from typing import Any

from voicehub_studio.config import AppPaths, SettingsStore
from voicehub_studio.db import Database, utc_now
from voicehub_studio.services.audio import process_audio
from voicehub_studio.services.hardware import resolve_device
from voicehub_studio.services.jobs import EventBus, JobCancelled, JobContext
from voicehub_studio.services.model_catalog import ModelCatalogService

REFERENCE_AUDIO_NAMES = (
    "speaker_audio_path",
    "reference_audio_path",
    "reference_audio",
    "audio_prompt_path",
    "prompt_wav_path",
    "reference_wav_path",
    "ref_audio",
)
REFERENCE_TEXT_NAMES = (
    "reference_text",
    "prompt_text",
    "ref_text",
)
DESIGN_NAMES = (
    "instruct",
    "description",
    "instruction",
    "voice_description",
)
PRESET_NAMES = ("speaker", "voice", "speaker_name", "voice_name")


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def _install_voicehub_compatibility(model_type: str, model: Any) -> None:
    """Bridge known public-API mismatches in the pinned VoiceHub revision."""
    if model_type != "qwen3tts" or getattr(
        model, "_voicehub_studio_qwen_input_bridge", False
    ):
        return

    # VoiceHub's native Qwen processor is keyword-only and tokenizes the text,
    # while Qwen's inference hook intentionally consumes the original text and
    # conditioning arguments. The inherited generic preparation method passes
    # text positionally and would also discard those conditioning arguments.
    def prepare_inputs_for_generation(
        instance: Any, text: str, **kwargs: Any
    ) -> dict[str, Any]:
        return {"text": text, **kwargs}

    model.prepare_inputs_for_generation = MethodType(
        prepare_inputs_for_generation, model
    )
    model._voicehub_studio_qwen_input_bridge = True


@dataclass(frozen=True)
class RuntimeKey:
    model_type: str
    checkpoint: str
    device: str
    model_config_hash: str
    optimization_hash: str

    @property
    def id(self) -> str:
        return _stable_hash(self.__dict__)


@dataclass
class RuntimeEntry:
    key: RuntimeKey
    model: Any
    loaded_at: float
    last_used_at: float
    busy: bool = False


class VoiceHubRuntimeManager:
    """LRU cache around VoiceHub's lazy TTS auto class."""

    def __init__(self, settings: SettingsStore, catalog: ModelCatalogService):
        self.settings_store = settings
        self.catalog = catalog
        self._models: OrderedDict[str, RuntimeEntry] = OrderedDict()
        self._lock = threading.RLock()

    def _key(
        self,
        model_type: str,
        checkpoint: str,
        device: str,
        model_config: dict[str, Any],
        optimization: dict[str, Any],
    ) -> RuntimeKey:
        return RuntimeKey(
            model_type=model_type,
            checkpoint=checkpoint,
            device=device,
            model_config_hash=_stable_hash(model_config),
            optimization_hash=_stable_hash(optimization),
        )

    def _optimization_config(self, values: dict[str, Any]):
        if not values:
            return None
        from voicehub import TTSOptimizationConfig

        aliases = {
            "attention": "attn_implementation",
            "kernel": "kernel_backend",
            "compile_policy": "compile",
        }
        normalized = {aliases.get(key, key): value for key, value in values.items()}
        if normalized.get("compile") is False:
            normalized["compile"] = "disabled"
        return TTSOptimizationConfig(**normalized)

    def _evict_if_needed(self, incoming_key: str) -> None:
        maximum = self.settings_store.load().max_loaded_models
        while len(self._models) >= maximum and incoming_key not in self._models:
            candidate_id = next(
                (
                    entry_id
                    for entry_id, entry in self._models.items()
                    if not entry.busy
                ),
                None,
            )
            if candidate_id is None:
                raise RuntimeError(
                    "Every loaded model is currently busy; try again when a job completes."
                )
            self._drop(candidate_id)

    def _drop(self, entry_id: str) -> None:
        entry = self._models.pop(entry_id, None)
        if entry is None:
            return
        model = entry.model
        for attribute in ("model", "runtime", "native_model", "processor"):
            if hasattr(model, attribute):
                try:
                    setattr(model, attribute, None)
                except Exception:
                    pass
        del model
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except Exception:
            pass

    def load(
        self,
        *,
        model_type: str,
        checkpoint: str,
        device: str,
        dtype: str,
        model_config: dict[str, Any],
        optimization: dict[str, Any],
        eager: bool,
    ) -> RuntimeEntry:
        self.catalog.get_model(model_type)
        resolved_device = resolve_device(device)
        if resolved_device.startswith("cuda"):
            try:
                import torch

                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "CUDA was requested, but this PyTorch installation cannot access the GPU."
                    )
            except ImportError as error:
                raise RuntimeError(
                    "CUDA generation requires a GPU-enabled PyTorch installation."
                ) from error

        config_values = dict(model_config)
        schema = self.catalog.generation_schema(model_type)
        config_names = {field["name"] for field in schema.get("model_config", [])}
        if dtype != "auto":
            if "torch_dtype" in config_names:
                config_values.setdefault("torch_dtype", dtype)
            elif "dtype" in config_names:
                config_values.setdefault("dtype", dtype)
        key = self._key(
            model_type, checkpoint, resolved_device, config_values, optimization
        )
        entry_id = key.id
        with self._lock:
            existing = self._models.get(entry_id)
            if existing is not None:
                existing.last_used_at = time.time()
                self._models.move_to_end(entry_id)
                if eager and not getattr(existing.model, "is_loaded", False):
                    existing.model.load()
                return existing
            self._evict_if_needed(entry_id)

            try:
                from voicehub import AutoModelForTextToSpeech
            except ImportError as error:
                raise RuntimeError(
                    "VoiceHub is not installed. Run the project bootstrap command before loading a model."
                ) from error
            optimization_config = self._optimization_config(optimization)
            kwargs: dict[str, Any] = {
                "model_type": model_type,
                "device": resolved_device,
                "lazy_load": True,
            }
            if config_values:
                kwargs["config_kwargs"] = config_values
            if optimization_config is not None:
                kwargs["optimization_config"] = optimization_config
            model = AutoModelForTextToSpeech.from_pretrained(checkpoint, **kwargs)
            _install_voicehub_compatibility(model_type, model)
            if eager:
                model.load()
            now = time.time()
            entry = RuntimeEntry(key=key, model=model, loaded_at=now, last_used_at=now)
            self._models[entry_id] = entry
            return entry

    def release(self, entry: RuntimeEntry) -> None:
        with self._lock:
            entry.busy = False
            entry.last_used_at = time.time()
            if entry.key.id in self._models:
                self._models.move_to_end(entry.key.id)

    def unload(self, entry_id: str | None = None) -> int:
        with self._lock:
            if entry_id is not None:
                if entry_id in self._models and self._models[entry_id].busy:
                    raise RuntimeError(
                        "The selected model is currently generating audio."
                    )
                existed = entry_id in self._models
                self._drop(entry_id)
                return int(existed)
            removable = [key for key, entry in self._models.items() if not entry.busy]
            for key in removable:
                self._drop(key)
            return len(removable)

    def unload_idle(self) -> int:
        minutes = self.settings_store.load().auto_unload_minutes
        if minutes <= 0:
            return 0
        cutoff = time.time() - minutes * 60
        with self._lock:
            stale = [
                key
                for key, entry in self._models.items()
                if not entry.busy and entry.last_used_at < cutoff
            ]
            for key in stale:
                self._drop(key)
            return len(stale)

    def status(self) -> dict[str, Any]:
        with self._lock:
            models = [
                {
                    "id": entry_id,
                    "model_type": entry.key.model_type,
                    "checkpoint": entry.key.checkpoint,
                    "device": entry.key.device,
                    "busy": entry.busy,
                    "loaded_at": entry.loaded_at,
                    "last_used_at": entry.last_used_at,
                    "loaded": bool(getattr(entry.model, "is_loaded", True)),
                }
                for entry_id, entry in self._models.items()
            ]
        return {"models": models, "count": len(models)}


def apply_voice_conditioning(
    schema: dict[str, Any],
    voice: dict[str, Any] | None,
    requested: dict[str, Any],
) -> dict[str, Any]:
    """Map a stored profile onto the selected model's declared fields."""
    if voice is None:
        return dict(requested)
    supported = {field["name"] for field in schema.get("conditioning", [])}
    conditioned = dict(voice.get("conditioning") or {})
    kind = voice.get("kind")
    reference_path = voice.get("reference_path")
    if kind in {"clone", "recording"} and reference_path:
        audio_name = next(
            (name for name in REFERENCE_AUDIO_NAMES if name in supported), None
        )
        if audio_name:
            conditioned.setdefault(audio_name, reference_path)
        text_name = next(
            (name for name in REFERENCE_TEXT_NAMES if name in supported), None
        )
        if text_name and voice.get("reference_text"):
            conditioned.setdefault(text_name, voice["reference_text"])
        if "mode" in supported:
            conditioned.setdefault("mode", "voice_clone")
    elif kind == "design" and voice.get("design_prompt"):
        design_name = next((name for name in DESIGN_NAMES if name in supported), None)
        if design_name:
            conditioned.setdefault(design_name, voice["design_prompt"])
        if "mode" in supported:
            conditioned.setdefault("mode", "voice_design")
    elif kind == "preset" and voice.get("speaker"):
        preset_name = next((name for name in PRESET_NAMES if name in supported), None)
        if preset_name:
            conditioned.setdefault(preset_name, voice["speaker"])
        if "mode" in supported:
            conditioned.setdefault("mode", "custom_voice")
    if voice.get("language") and "language" in supported:
        conditioned.setdefault("language", voice["language"])
    conditioned.update(requested)
    return conditioned


class GenerationService:
    """Job handler that turns persisted requests into normalized audio assets."""

    def __init__(
        self,
        database: Database,
        paths: AppPaths,
        runtime: VoiceHubRuntimeManager,
        catalog: ModelCatalogService,
        events: EventBus,
    ):
        self.database = database
        self.paths = paths
        self.runtime = runtime
        self.catalog = catalog
        self.events = events

    def handle(self, context: JobContext, payload: dict[str, Any]) -> dict[str, Any]:
        generation_id = payload["generation_id"]
        generation = self.database.get("generations", generation_id)
        if generation is None:
            raise KeyError(f"Generation {generation_id!r} no longer exists.")
        started_at = utc_now()
        self._update_generation(
            generation_id,
            status="running",
            started_at=started_at,
            error=None,
        )
        started = time.perf_counter()
        entry: RuntimeEntry | None = None
        raw_path = self.paths.generations / f"{generation_id}.raw.wav"
        final_path = (
            self.paths.generations / f"{generation_id}.{generation['output_format']}"
        )
        try:
            context.update(0.06, "Preparing VoiceHub runtime")
            entry = self.runtime.load(
                model_type=generation["model_type"],
                checkpoint=generation["checkpoint"],
                device=generation["device"],
                dtype=generation.get("dtype") or "auto",
                model_config=generation["model_config"],
                optimization=generation["optimization"],
                eager=False,
            )
            with self.runtime._lock:
                entry.busy = True
            context.update(0.16, "Loading model weights")
            entry.model.load()
            context.update(0.42, "Synthesizing speech")
            generation_config_values = dict(generation["generation_config"])
            generation_config_values["output_file"] = str(raw_path)
            from voicehub import TTSGenerationConfig

            generation_config = TTSGenerationConfig(**generation_config_values)
            output = entry.model.generate(
                generation["text"],
                generation_config=generation_config,
                **generation["model_kwargs"],
            )
            context.check_cancelled()
            if not raw_path.is_file():
                output.save(raw_path)
            context.update(0.82, "Finalizing audio")
            request_options = payload.get("output", {})
            operations = []
            if request_options.get("normalize"):
                operations.append({"op": "normalize", "target_lufs": -16})
            details = process_audio(
                raw_path,
                final_path,
                operations,
                output_format=generation["output_format"],
                sample_rate=request_options.get("sample_rate"),
                channels=request_options.get("channels", 1),
            )
            raw_path.unlink(missing_ok=True)
            latency = time.perf_counter() - started
            metadata = dict(_json_safe(getattr(output, "metadata", {})))
            metadata.update(
                {
                    "voicehub_sample_rate": int(output.sample_rate),
                    "resolved_device": entry.key.device,
                    "runtime_id": entry.key.id,
                }
            )
            updated = self._update_generation(
                generation_id,
                status="completed",
                output_path=str(final_path),
                sample_rate=details["sample_rate"],
                duration=details["duration"],
                latency=latency,
                metadata=metadata,
                completed_at=utc_now(),
            )
            context.update(0.98, "Saving generation history")
            return {
                "generation_id": generation_id,
                "output_path": str(final_path),
                "generation": updated,
            }
        except Exception as error:
            raw_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            self._update_generation(
                generation_id,
                status="cancelled" if isinstance(error, JobCancelled) else "failed",
                error=str(error)[-8000:],
                completed_at=utc_now(),
            )
            raise
        finally:
            if entry is not None:
                self.runtime.release(entry)

    def preload(self, context: JobContext, payload: dict[str, Any]) -> dict[str, Any]:
        context.update(0.08, "Preparing model")
        entry = self.runtime.load(
            model_type=payload["model_type"],
            checkpoint=payload["checkpoint"],
            device=payload.get("device", "auto"),
            dtype=payload.get("dtype", "auto"),
            model_config=payload.get("model_config", {}),
            optimization=payload.get("optimization", {}),
            eager=False,
        )
        context.update(0.2, "Downloading and loading weights")
        entry.model.load()
        context.update(0.95, "Model ready")
        return {
            "runtime_id": entry.key.id,
            "model_type": entry.key.model_type,
            "device": entry.key.device,
        }

    def _update_generation(
        self, generation_id: str, **values: Any
    ) -> dict[str, Any] | None:
        updated = self.database.update("generations", generation_id, values)
        if updated:
            self.events.publish("generation.updated", updated)
        return updated
