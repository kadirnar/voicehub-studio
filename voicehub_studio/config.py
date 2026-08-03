"""Application paths and persisted runtime settings."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from threading import RLock
from typing import Any

APP_SLUG = "voicehub-studio"


def _xdg_path(environment_name: str, fallback: Path) -> Path:
    configured = os.environ.get(environment_name)
    return Path(configured).expanduser() if configured else fallback


@dataclass(frozen=True)
class AppPaths:
    """All mutable paths used by the application."""

    data: Path
    config: Path
    cache: Path
    database: Path
    voices: Path
    assets: Path
    generations: Path
    training: Path
    logs: Path

    @classmethod
    def discover(cls) -> AppPaths:
        override = os.environ.get("VOICEHUB_STUDIO_HOME")
        if override:
            data = Path(override).expanduser().resolve()
            config_root = data / "config"
            cache = data / "cache"
        else:
            home = Path.home()
            data = _xdg_path("XDG_DATA_HOME", home / ".local" / "share") / APP_SLUG
            config_root = _xdg_path("XDG_CONFIG_HOME", home / ".config") / APP_SLUG
            cache = _xdg_path("XDG_CACHE_HOME", home / ".cache") / APP_SLUG
        return cls(
            data=data,
            config=config_root,
            cache=cache,
            database=data / "studio.sqlite3",
            voices=data / "voices",
            assets=data / "assets",
            generations=data / "generations",
            training=data / "training",
            logs=data / "logs",
        )

    def ensure(self) -> AppPaths:
        for path in (
            self.data,
            self.config,
            self.cache,
            self.voices,
            self.assets,
            self.generations,
            self.training,
            self.logs,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return self


@dataclass
class StudioSettings:
    """User-editable defaults; request-level values can override all fields."""

    default_device: str = "auto"
    default_dtype: str = "auto"
    default_model_type: str = "qwen3tts"
    default_checkpoint: str = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
    default_language: str = "Auto"
    output_format: str = "wav"
    output_sample_rate: int | None = None
    output_channels: int = 1
    max_loaded_models: int = 1
    max_upload_mb: int = 500
    queue_workers: int = 1
    auto_unload_minutes: int = 15
    attn_implementation: str = "auto"
    kernel_backend: str = "auto"
    compile_policy: str = "disabled"
    bind_host: str = "127.0.0.1"
    port: int = 8765
    open_mode: str = "window"
    theme: str = "dark"
    interface_language: str = "system"

    def validate(self) -> None:
        if self.default_device not in {
            "auto",
            "cpu",
            "cuda",
            "mps",
            "xpu",
        } and not self.default_device.startswith("cuda:"):
            raise ValueError("Unsupported default device.")
        if self.default_dtype not in {"auto", "float32", "float16", "bfloat16"}:
            raise ValueError("Unsupported default dtype.")
        if self.output_format not in {"wav", "flac", "mp3", "ogg"}:
            raise ValueError("Unsupported output format.")
        if self.output_channels not in {1, 2}:
            raise ValueError("Output channels must be 1 or 2.")
        if not 1 <= self.max_loaded_models <= 8:
            raise ValueError("max_loaded_models must be between 1 and 8.")
        if not 1 <= self.queue_workers <= 8:
            raise ValueError("queue_workers must be between 1 and 8.")
        if not 1 <= self.max_upload_mb <= 10_000:
            raise ValueError("max_upload_mb must be between 1 and 10000.")
        if not 0 <= self.auto_unload_minutes <= 24 * 60:
            raise ValueError("auto_unload_minutes is outside the supported range.")
        if self.attn_implementation not in {
            "auto",
            "native",
            "sdpa",
            "flash_attention_4",
        }:
            raise ValueError("Unsupported attention implementation.")
        if self.kernel_backend not in {
            "auto",
            "native",
            "torch",
            "triton",
            "cuda_extension",
        }:
            raise ValueError("Unsupported kernel backend.")
        if self.compile_policy not in {"auto", "required", "disabled"}:
            raise ValueError("Unsupported compile policy.")
        if not 1 <= self.port <= 65_535:
            raise ValueError("Port is outside the supported range.")
        if self.open_mode not in {"window", "browser", "server"}:
            raise ValueError("Unsupported open mode.")
        if self.theme not in {"dark", "light", "system"}:
            raise ValueError("Unsupported theme.")
        if self.interface_language not in {"system", "en", "tr"}:
            raise ValueError("Unsupported interface language.")


class SettingsStore:
    """Small atomic JSON settings store guarded for API and worker threads."""

    def __init__(self, paths: AppPaths):
        self.paths = paths
        self.path = paths.config / "settings.json"
        self._lock = RLock()

    def load(self) -> StudioSettings:
        with self._lock:
            if not self.path.is_file():
                settings = StudioSettings()
                settings.validate()
                return settings
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            allowed = {field.name for field in fields(StudioSettings)}
            settings = StudioSettings(
                **{key: value for key, value in payload.items() if key in allowed}
            )
            settings.validate()
            return settings

    def update(self, values: dict[str, Any]) -> StudioSettings:
        with self._lock:
            current = asdict(self.load())
            allowed = {field.name for field in fields(StudioSettings)}
            unknown = sorted(set(values) - allowed)
            if unknown:
                raise ValueError(f"Unknown settings: {', '.join(unknown)}")
            current.update(values)
            settings = StudioSettings(**current)
            settings.validate()
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(asdict(settings), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.path)
            return settings
