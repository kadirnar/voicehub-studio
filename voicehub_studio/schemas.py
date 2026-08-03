"""Validated API request contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class VoiceCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["clone", "design", "preset", "recording"]
    model_type: str | None = Field(default=None, max_length=100)
    checkpoint: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, max_length=100)
    speaker: str | None = Field(default=None, max_length=200)
    reference_asset_id: str | None = None
    reference_text: str | None = Field(default=None, max_length=20_000)
    design_prompt: str | None = Field(default=None, max_length=8_000)
    conditioning: dict[str, JsonValue] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list, max_length=32)
    favorite: bool = False
    consent_confirmed: bool = False
    consent_note: str | None = Field(default=None, max_length=2_000)
    source_uri: str | None = Field(default=None, max_length=2_000)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))
        if any(len(tag) > 40 for tag in cleaned):
            raise ValueError("Tags must be at most 40 characters.")
        return cleaned

    @model_validator(mode="after")
    def validate_kind_requirements(self) -> VoiceCreate:
        if self.kind in {"clone", "recording"}:
            if not self.reference_asset_id:
                raise ValueError(
                    "A reference audio asset is required for cloned or recorded voices."
                )
            if not self.consent_confirmed:
                raise ValueError(
                    "Voice authorization must be confirmed before saving a reference voice."
                )
        if self.kind == "design" and not self.design_prompt:
            raise ValueError("A voice design description is required.")
        if self.kind == "preset" and not self.speaker:
            raise ValueError("A preset speaker or voice name is required.")
        return self


class VoiceUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    model_type: str | None = Field(default=None, max_length=100)
    checkpoint: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, max_length=100)
    speaker: str | None = Field(default=None, max_length=200)
    reference_asset_id: str | None = None
    reference_text: str | None = Field(default=None, max_length=20_000)
    design_prompt: str | None = Field(default=None, max_length=8_000)
    conditioning: dict[str, JsonValue] | None = None
    tags: list[str] | None = Field(default=None, max_length=32)
    favorite: bool | None = None
    consent_confirmed: bool | None = None
    consent_note: str | None = Field(default=None, max_length=2_000)
    source_uri: str | None = Field(default=None, max_length=2_000)


class GenerationRequest(StrictModel):
    text: str = Field(min_length=1, max_length=200_000)
    model_type: str = Field(min_length=1, max_length=100)
    checkpoint: str = Field(min_length=1, max_length=1_000)
    voice_id: str | None = None
    device: str = Field(default="auto", max_length=40)
    dtype: Literal["auto", "float32", "float16", "bfloat16"] = "auto"
    generation_config: dict[str, JsonValue] = Field(default_factory=dict)
    model_kwargs: dict[str, JsonValue] = Field(default_factory=dict)
    model_config_values: dict[str, JsonValue] = Field(
        default_factory=dict, alias="model_config"
    )
    optimization: dict[str, JsonValue] = Field(default_factory=dict)
    output_format: Literal["wav", "flac", "mp3", "ogg"] = "wav"
    output_sample_rate: int | None = Field(default=None, ge=8_000, le=192_000)
    output_channels: Literal[1, 2] = 1
    normalize_output: bool = False

    @field_validator("device")
    @classmethod
    def validate_device(cls, value: str) -> str:
        allowed = {"auto", "cpu", "cuda", "mps", "xpu"}
        if value not in allowed and not value.startswith("cuda:"):
            raise ValueError("Device must be auto, cpu, cuda, cuda:N, mps, or xpu.")
        return value


class ModelLoadRequest(StrictModel):
    checkpoint: str = Field(min_length=1, max_length=1_000)
    device: str = Field(default="auto", max_length=40)
    dtype: Literal["auto", "float32", "float16", "bfloat16"] = "auto"
    model_config_values: dict[str, JsonValue] = Field(
        default_factory=dict, alias="model_config"
    )
    optimization: dict[str, JsonValue] = Field(default_factory=dict)


class AudioEditRequest(StrictModel):
    source_asset_id: str
    name: str | None = Field(default=None, max_length=200)
    operations: list[dict[str, JsonValue]] = Field(min_length=1, max_length=100)
    output_format: Literal["wav", "flac", "mp3", "ogg"] = "wav"
    sample_rate: int | None = Field(default=None, ge=8_000, le=192_000)
    channels: Literal[1, 2] | None = None


class AudioConcatRequest(StrictModel):
    asset_ids: list[str] = Field(min_length=2, max_length=100)
    name: str = Field(default="Combined audio", min_length=1, max_length=200)
    crossfade: float = Field(default=0.0, ge=0.0, le=10.0)
    output_format: Literal["wav", "flac", "mp3", "ogg"] = "wav"


class TrainingRequest(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    model_type: str = Field(min_length=1, max_length=100)
    checkpoint: str = Field(min_length=1, max_length=1_000)
    train_manifest: str = Field(min_length=1, max_length=4_000)
    eval_manifest: str | None = Field(default=None, max_length=4_000)
    output_dir: str | None = Field(default=None, max_length=4_000)
    device: str = Field(default="auto", max_length=40)
    config: dict[str, JsonValue] = Field(default_factory=dict)


class ProjectCreate(StrictModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4_000)
    sample_rate: int = Field(default=48_000, ge=8_000, le=192_000)
