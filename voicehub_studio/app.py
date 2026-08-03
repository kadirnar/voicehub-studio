"""FastAPI application for the local VoiceHub Studio desktop client."""

from __future__ import annotations

import asyncio
import json
import mimetypes
import sqlite3
import tempfile
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from voicehub_studio import __version__
from voicehub_studio.config import AppPaths, SettingsStore
from voicehub_studio.db import Database, new_id, utc_now
from voicehub_studio.schemas import (
    AudioConcatRequest,
    AudioEditRequest,
    GenerationRequest,
    ModelLoadRequest,
    ProjectCreate,
    TrainingRequest,
    VoiceCreate,
    VoiceUpdate,
)
from voicehub_studio.services.audio import (
    AudioProcessingError,
    concatenate_audio,
    copy_uploaded_audio,
    detect_speech_segments,
    process_audio,
    unique_audio_path,
    validate_audio_upload,
    waveform_peaks,
)
from voicehub_studio.services.hardware import inspect_hardware
from voicehub_studio.services.jobs import EventBus, JobContext, JobQueue
from voicehub_studio.services.model_catalog import ModelCatalogService
from voicehub_studio.services.runtime import (
    REFERENCE_AUDIO_NAMES,
    GenerationService,
    VoiceHubRuntimeManager,
    apply_voice_conditioning,
)
from voicehub_studio.services.training import TrainingService

STATIC_DIR = Path(__file__).with_name("static")


class ApplicationState:
    """Long-lived process services shared by API routes and desktop shell."""

    def __init__(self, paths: AppPaths | None = None):
        self.paths = (paths or AppPaths.discover()).ensure()
        self.settings = SettingsStore(self.paths)
        self.database = Database(self.paths.database)
        self.events = EventBus()
        self.catalog = ModelCatalogService()
        self.runtime = VoiceHubRuntimeManager(self.settings, self.catalog)
        self.generation = GenerationService(
            self.database,
            self.paths,
            self.runtime,
            self.catalog,
            self.events,
        )
        self.training = TrainingService(
            self.database,
            self.paths,
            self.runtime,
            self.events,
        )
        self.jobs = JobQueue(
            self.database,
            self.events,
            workers=self.settings.load().queue_workers,
        )
        self.jobs.register("tts.generate", self.generation.handle)
        self.jobs.register("model.load", self.generation.preload)
        self.jobs.register("audio.edit", self._edit_audio)
        self.jobs.register("audio.concat", self._concat_audio)
        self.jobs.register("model.train", self.training.handle)

    def _edit_audio(
        self, context: JobContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        source = self.database.get("assets", payload["source_asset_id"])
        if source is None:
            raise KeyError(f"Audio asset {payload['source_asset_id']!r} was not found.")
        context.update(0.08, "Preparing edit")
        output_format = payload["output_format"]
        destination = unique_audio_path(
            self.paths.assets,
            payload.get("name") or f"{source['name']} edit",
            output_format,
        )
        context.update(0.18, "Rendering audio effects")
        details = process_audio(
            source["path"],
            destination,
            payload["operations"],
            output_format=output_format,
            sample_rate=payload.get("sample_rate"),
            channels=payload.get("channels"),
        )
        context.update(0.9, "Saving audio asset")
        asset = self.database.create_asset(
            {
                "name": payload.get("name") or f"{source['name']} edit",
                "path": destination,
                "kind": "edit",
                "parent_id": source["id"],
                "operations": payload["operations"],
                **details,
            }
        )
        self.events.publish("asset.created", asset)
        return {"asset": asset}

    def _concat_audio(
        self, context: JobContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        assets = []
        for asset_id in payload["asset_ids"]:
            asset = self.database.get("assets", asset_id)
            if asset is None:
                raise KeyError(f"Audio asset {asset_id!r} was not found.")
            assets.append(asset)
        context.update(0.08, "Preparing clips")
        destination = unique_audio_path(
            self.paths.assets,
            payload["name"],
            payload["output_format"],
        )
        context.update(0.2, "Combining clips")
        details = concatenate_audio(
            [asset["path"] for asset in assets],
            destination,
            output_format=payload["output_format"],
            crossfade=payload.get("crossfade", 0),
        )
        context.update(0.9, "Saving combined asset")
        asset = self.database.create_asset(
            {
                "name": payload["name"],
                "path": destination,
                "kind": "combined",
                "operations": [
                    {
                        "op": "concat",
                        "asset_ids": payload["asset_ids"],
                        "crossfade": payload.get("crossfade", 0),
                    }
                ],
                **details,
            }
        )
        self.events.publish("asset.created", asset)
        return {"asset": asset}


def _not_found(record_type: str, record_id: str) -> HTTPException:
    return HTTPException(
        status_code=404, detail=f"{record_type} {record_id!r} was not found."
    )


def _asset_with_urls(asset: dict[str, Any]) -> dict[str, Any]:
    return {
        **asset,
        "content_url": f"/api/assets/{asset['id']}/content",
        "waveform_url": f"/api/assets/{asset['id']}/waveform",
    }


def _generation_with_url(generation: dict[str, Any]) -> dict[str, Any]:
    item = dict(generation)
    item["audio_url"] = (
        f"/api/generations/{generation['id']}/audio"
        if generation.get("status") == "completed" and generation.get("output_path")
        else None
    )
    return item


def _resolve_asset_conditioning(
    state: ApplicationState,
    schema: dict[str, Any],
    values: dict[str, Any],
) -> dict[str, Any]:
    controls = {
        field["name"]: field.get("control") for field in schema.get("conditioning", [])
    }
    resolved = dict(values)
    for name, value in list(resolved.items()):
        if controls.get(name) != "asset" and name not in REFERENCE_AUDIO_NAMES:
            continue
        if not isinstance(value, str) or not value:
            continue
        asset_id = value.removeprefix("asset:")
        asset = state.database.get("assets", asset_id)
        if asset is not None:
            resolved[name] = asset["path"]
        elif value.startswith("asset:"):
            raise ValueError(f"Audio asset {asset_id!r} was not found.")
    return resolved


async def _save_upload(upload: UploadFile, maximum_bytes: int) -> tuple[Path, int]:
    suffix = Path(upload.filename or "audio.wav").suffix
    temporary = tempfile.NamedTemporaryFile(
        prefix="voicehub-studio-upload-",
        suffix=suffix,
        delete=False,
    )
    size = 0
    path = Path(temporary.name)
    try:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > maximum_bytes:
                raise ValueError("The upload exceeds the configured size limit.")
            temporary.write(chunk)
        temporary.flush()
        temporary.close()
        return path, size
    except Exception:
        temporary.close()
        path.unlink(missing_ok=True)
        raise


def create_app(paths: AppPaths | None = None) -> FastAPI:
    state = ApplicationState(paths)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        state.jobs.start()
        state.events.publish("app.started", {"version": __version__})
        yield
        state.runtime.unload()
        state.jobs.shutdown(wait=False)

    app = FastAPI(
        title="VoiceHub Studio",
        description="Local-first VoiceHub TTS, cloning, design, editing, and training studio.",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.studio = state

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, error: KeyError):
        return JSONResponse(status_code=404, content={"detail": str(error).strip("'")})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, error: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(error)})

    @app.exception_handler(AudioProcessingError)
    async def audio_error_handler(request: Request, error: AudioProcessingError):
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(sqlite3.IntegrityError)
    async def database_error_handler(request: Request, error: sqlite3.IntegrityError):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "voicehub_available": state.catalog.voicehub_available,
            "voicehub_version": state.catalog.voicehub_version,
        }

    @app.get("/api/system")
    def system_status() -> dict[str, Any]:
        return {
            **inspect_hardware(state.paths.data),
            "app": {
                "version": __version__,
                "paths": {
                    key: str(value) for key, value in asdict(state.paths).items()
                },
            },
            "runtime": state.runtime.status(),
        }

    @app.get("/api/settings")
    def get_settings() -> dict[str, Any]:
        return asdict(state.settings.load())

    @app.put("/api/settings")
    def update_settings(values: dict[str, Any] = Body(...)) -> dict[str, Any]:
        settings = state.settings.update(values)
        state.events.publish("settings.updated", asdict(settings))
        return asdict(settings)

    @app.get("/api/models")
    def list_models(
        capability: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        models = state.catalog.list_models()
        if capability:
            models = [model for model in models if capability in model["capabilities"]]
        if search:
            needle = search.casefold()
            models = [
                model
                for model in models
                if needle in model["model_type"].casefold()
                or needle in model["display_name"].casefold()
                or needle in model["default_checkpoint"].casefold()
            ]
        return {
            "items": models,
            "count": len(models),
            "voicehub_version": state.catalog.voicehub_version,
            "dynamic": state.catalog.voicehub_available,
        }

    @app.get("/api/models/{model_type}")
    def model_details(model_type: str) -> dict[str, Any]:
        return state.catalog.generation_schema(model_type)

    @app.post("/api/models/{model_type}/load", status_code=202)
    def load_model(model_type: str, request: ModelLoadRequest) -> dict[str, Any]:
        state.catalog.get_model(model_type)
        payload = request.model_dump(by_alias=True)
        payload["model_type"] = model_type
        return state.jobs.submit("model.load", payload)

    @app.get("/api/runtime")
    def runtime_status() -> dict[str, Any]:
        state.runtime.unload_idle()
        return state.runtime.status()

    @app.delete("/api/runtime")
    def unload_runtime(runtime_id: str | None = None) -> dict[str, Any]:
        removed = state.runtime.unload(runtime_id)
        state.events.publish(
            "runtime.unloaded", {"runtime_id": runtime_id, "count": removed}
        )
        return {"removed": removed, **state.runtime.status()}

    @app.get("/api/voices")
    def list_voices(limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
        voices = state.database.list("voices", limit=limit)
        for voice in voices:
            if voice.get("reference_asset_id"):
                voice["reference_audio_url"] = (
                    f"/api/assets/{voice['reference_asset_id']}/content"
                )
        return {"items": voices, "count": len(voices)}

    @app.post("/api/voices", status_code=201)
    def create_voice(request: VoiceCreate) -> dict[str, Any]:
        values = request.model_dump()
        if (
            values.get("reference_asset_id")
            and state.database.get("assets", values["reference_asset_id"]) is None
        ):
            raise _not_found("Audio asset", values["reference_asset_id"])
        voice = state.database.create_voice(values)
        state.events.publish("voice.created", voice)
        return voice

    @app.patch("/api/voices/{voice_id}")
    def update_voice(voice_id: str, request: VoiceUpdate) -> dict[str, Any]:
        if state.database.get("voices", voice_id) is None:
            raise _not_found("Voice", voice_id)
        values = request.model_dump(exclude_unset=True)
        reference_id = values.get("reference_asset_id")
        if reference_id and state.database.get("assets", reference_id) is None:
            raise _not_found("Audio asset", reference_id)
        values["updated_at"] = utc_now()
        voice = state.database.update("voices", voice_id, values)
        assert voice is not None
        state.events.publish("voice.updated", voice)
        return voice

    @app.delete("/api/voices/{voice_id}", status_code=204)
    def delete_voice(voice_id: str):
        if not state.database.delete("voices", voice_id):
            raise _not_found("Voice", voice_id)
        state.events.publish("voice.deleted", {"id": voice_id})

    @app.get("/api/assets")
    def list_assets(limit: int = Query(300, ge=1, le=1000)) -> dict[str, Any]:
        assets = [
            _asset_with_urls(asset)
            for asset in state.database.list("assets", limit=limit)
        ]
        return {"items": assets, "count": len(assets)}

    @app.post("/api/assets", status_code=201)
    async def upload_asset(
        file: UploadFile = File(...),
        name: str | None = Form(default=None),
        kind: str = Form(default="audio"),
    ) -> dict[str, Any]:
        settings = state.settings.load()
        filename = file.filename or "audio.wav"
        maximum_bytes = settings.max_upload_mb * 1024 * 1024
        temporary, size = await _save_upload(file, maximum_bytes)
        try:
            validate_audio_upload(filename, size, settings.max_upload_mb)
            destination, details = copy_uploaded_audio(
                temporary, state.paths.assets, filename
            )
            asset = state.database.create_asset(
                {
                    "name": name or Path(filename).stem,
                    "path": destination,
                    "kind": kind,
                    "metadata": {"original_filename": filename, "uploaded_size": size},
                    **details,
                }
            )
        finally:
            temporary.unlink(missing_ok=True)
            await file.close()
        state.events.publish("asset.created", asset)
        return _asset_with_urls(asset)

    @app.get("/api/assets/{asset_id}")
    def get_asset(asset_id: str) -> dict[str, Any]:
        asset = state.database.get("assets", asset_id)
        if asset is None:
            raise _not_found("Audio asset", asset_id)
        return _asset_with_urls(asset)

    @app.get("/api/assets/{asset_id}/content")
    def asset_content(asset_id: str):
        asset = state.database.get("assets", asset_id)
        if asset is None:
            raise _not_found("Audio asset", asset_id)
        path = Path(asset["path"])
        if not path.is_file():
            raise HTTPException(
                status_code=410, detail="The audio file is missing from storage."
            )
        return FileResponse(
            path,
            media_type=asset.get("mime_type")
            or mimetypes.guess_type(path.name)[0]
            or "audio/wav",
            content_disposition_type="inline",
        )

    @app.get("/api/assets/{asset_id}/waveform")
    def asset_waveform(
        asset_id: str, buckets: int = Query(1200, ge=64, le=10_000)
    ) -> dict[str, Any]:
        asset = state.database.get("assets", asset_id)
        if asset is None:
            raise _not_found("Audio asset", asset_id)
        return waveform_peaks(asset["path"], buckets=buckets)

    @app.get("/api/assets/{asset_id}/segments")
    def asset_segments(
        asset_id: str,
        threshold_db: float = Query(-42, ge=-90, le=-5),
        minimum_silence: float = Query(0.35, ge=0.05, le=10),
        padding: float = Query(0.08, ge=0, le=2),
    ) -> dict[str, Any]:
        asset = state.database.get("assets", asset_id)
        if asset is None:
            raise _not_found("Audio asset", asset_id)
        segments = detect_speech_segments(
            asset["path"],
            threshold_db=threshold_db,
            minimum_silence=minimum_silence,
            padding=padding,
        )
        return {
            "asset_id": asset_id,
            "method": "ffmpeg-silencedetect",
            "segments": segments,
        }

    @app.delete("/api/assets/{asset_id}", status_code=204)
    def delete_asset(asset_id: str):
        asset = state.database.get("assets", asset_id)
        if asset is None:
            raise _not_found("Audio asset", asset_id)
        if not state.database.delete("assets", asset_id):
            raise _not_found("Audio asset", asset_id)
        path = Path(asset["path"])
        try:
            path.resolve().relative_to(state.paths.data.resolve())
            path.unlink(missing_ok=True)
        except ValueError:
            pass
        state.events.publish("asset.deleted", {"id": asset_id})

    @app.post("/api/audio/edit", status_code=202)
    def edit_audio(request: AudioEditRequest) -> dict[str, Any]:
        if state.database.get("assets", request.source_asset_id) is None:
            raise _not_found("Audio asset", request.source_asset_id)
        return state.jobs.submit("audio.edit", request.model_dump())

    @app.post("/api/audio/concat", status_code=202)
    def concat_audio(request: AudioConcatRequest) -> dict[str, Any]:
        return state.jobs.submit("audio.concat", request.model_dump())

    @app.post("/api/generations", status_code=202)
    def create_generation(request: GenerationRequest) -> dict[str, Any]:
        schema = state.catalog.generation_schema(request.model_type)
        voice = None
        if request.voice_id:
            voice = state.database.get("voices", request.voice_id)
            if voice is None:
                raise _not_found("Voice", request.voice_id)
            if voice.get("reference_asset_id"):
                asset = state.database.get("assets", voice["reference_asset_id"])
                if asset is None:
                    raise ValueError(
                        "The voice profile's reference audio no longer exists."
                    )
                voice = {**voice, "reference_path": asset["path"]}
        requested_kwargs = _resolve_asset_conditioning(
            state, schema, dict(request.model_kwargs)
        )
        model_kwargs = apply_voice_conditioning(schema, voice, requested_kwargs)
        generation = state.database.create_generation(
            {
                "text": request.text,
                "model_type": request.model_type,
                "checkpoint": request.checkpoint,
                "voice_id": request.voice_id,
                "device": request.device,
                "dtype": request.dtype,
                "generation_config": request.generation_config,
                "model_kwargs": model_kwargs,
                "model_config": request.model_config_values,
                "optimization": request.optimization,
                "output_format": request.output_format,
            }
        )
        job = state.jobs.submit(
            "tts.generate",
            {
                "generation_id": generation["id"],
                "output": {
                    "sample_rate": request.output_sample_rate,
                    "channels": request.output_channels,
                    "normalize": request.normalize_output,
                },
            },
        )
        generation = state.database.update(
            "generations",
            generation["id"],
            {"job_id": job["id"]},
        )
        assert generation is not None
        state.events.publish("generation.created", generation)
        return {"generation": _generation_with_url(generation), "job": job}

    @app.get("/api/generations")
    def list_generations(limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
        generations = [
            _generation_with_url(item)
            for item in state.database.list("generations", limit=limit)
        ]
        return {"items": generations, "count": len(generations)}

    @app.get("/api/generations/{generation_id}")
    def get_generation(generation_id: str) -> dict[str, Any]:
        generation = state.database.get("generations", generation_id)
        if generation is None:
            raise _not_found("Generation", generation_id)
        return _generation_with_url(generation)

    @app.get("/api/generations/{generation_id}/audio")
    def generation_audio(generation_id: str):
        generation = state.database.get("generations", generation_id)
        if generation is None:
            raise _not_found("Generation", generation_id)
        if generation["status"] != "completed" or not generation.get("output_path"):
            raise HTTPException(
                status_code=409, detail="Generation audio is not ready."
            )
        path = Path(generation["output_path"])
        if not path.is_file():
            raise HTTPException(
                status_code=410, detail="The generated file is missing from storage."
            )
        return FileResponse(
            path,
            media_type=mimetypes.guess_type(path.name)[0] or "audio/wav",
            filename=path.name,
            content_disposition_type="inline",
        )

    @app.delete("/api/generations/{generation_id}", status_code=204)
    def delete_generation(generation_id: str):
        generation = state.database.get("generations", generation_id)
        if generation is None:
            raise _not_found("Generation", generation_id)
        if generation["status"] in {"queued", "running"}:
            raise HTTPException(
                status_code=409, detail="Cancel the active job before deleting it."
            )
        if generation.get("output_path"):
            Path(generation["output_path"]).unlink(missing_ok=True)
        state.database.delete("generations", generation_id)
        state.events.publish("generation.deleted", {"id": generation_id})

    @app.get("/api/jobs")
    def list_jobs(limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
        jobs = state.database.list("jobs", limit=limit)
        return {"items": jobs, "count": len(jobs)}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = state.database.get("jobs", job_id)
        if job is None:
            raise _not_found("Job", job_id)
        return job

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, Any]:
        try:
            return state.jobs.cancel(job_id)
        except KeyError:
            raise _not_found("Job", job_id)

    @app.get("/api/events")
    async def stream_events(request: Request, cursor: int = Query(0, ge=0)):
        header_cursor = request.headers.get("last-event-id")
        if header_cursor and header_cursor.isdigit():
            cursor = max(cursor, int(header_cursor))

        async def event_stream():
            nonlocal cursor
            idle_ticks = 0
            while not await request.is_disconnected():
                events = state.events.since(cursor)
                if events:
                    for event in events:
                        cursor = event["id"]
                        yield (
                            f"id: {event['id']}\n"
                            f"event: {event['kind']}\n"
                            f"data: {json.dumps(event['payload'], ensure_ascii=False, default=str)}\n\n"
                        )
                    idle_ticks = 0
                else:
                    idle_ticks += 1
                    if idle_ticks >= 15:
                        yield ": keep-alive\n\n"
                        idle_ticks = 0
                await asyncio.sleep(1)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/training")
    def list_training(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
        items = state.database.list("training_runs", limit=limit)
        return {"items": items, "count": len(items)}

    @app.post("/api/training", status_code=202)
    def create_training(request: TrainingRequest) -> dict[str, Any]:
        state.catalog.get_model(request.model_type)
        output_dir = request.output_dir or str(state.paths.training / new_id("run"))
        training = state.database.create_training_run(
            {
                **request.model_dump(),
                "output_dir": output_dir,
            }
        )
        job = state.jobs.submit("model.train", {"training_id": training["id"]})
        training = state.database.update(
            "training_runs",
            training["id"],
            {"job_id": job["id"]},
        )
        assert training is not None
        state.events.publish("training.created", training)
        return {"training": training, "job": job}

    @app.get("/api/training/{training_id}")
    def get_training(training_id: str) -> dict[str, Any]:
        training = state.database.get("training_runs", training_id)
        if training is None:
            raise _not_found("Training run", training_id)
        return training

    @app.get("/api/projects")
    def list_projects(limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
        projects = state.database.list("projects", limit=limit)
        return {"items": projects, "count": len(projects)}

    @app.post("/api/projects", status_code=201)
    def create_project(request: ProjectCreate) -> dict[str, Any]:
        now = utc_now()
        project = state.database._insert(
            "projects",
            {
                "id": new_id("project"),
                **request.model_dump(),
                "created_at": now,
                "updated_at": now,
            },
        )
        state.events.publish("project.created", project)
        return project

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{client_path:path}", include_in_schema=False)
    def client_router(client_path: str):
        if client_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found.")
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
