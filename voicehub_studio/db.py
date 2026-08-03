"""SQLite persistence for voices, assets, jobs, and reproducible requests."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

JSON_COLUMNS = {
    "tags",
    "conditioning",
    "metadata",
    "operations",
    "generation_config",
    "model_kwargs",
    "model_config",
    "optimization",
    "payload",
    "result",
    "config",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _decode_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    for key in JSON_COLUMNS.intersection(item):
        value = item[key]
        if value is not None and isinstance(value, str):
            try:
                item[key] = json.loads(value)
            except json.JSONDecodeError:
                item[key] = value
    for key in ("favorite", "consent_confirmed", "cancel_requested"):
        if key in item and item[key] is not None:
            item[key] = bool(item[key])
    return item


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS voices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('clone', 'design', 'preset', 'recording')),
    model_type TEXT,
    checkpoint TEXT,
    language TEXT,
    speaker TEXT,
    reference_asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    reference_text TEXT,
    design_prompt TEXT,
    conditioning TEXT NOT NULL DEFAULT '{}',
    tags TEXT NOT NULL DEFAULT '[]',
    favorite INTEGER NOT NULL DEFAULT 0,
    consent_confirmed INTEGER NOT NULL DEFAULT 0,
    consent_note TEXT,
    source_uri TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL DEFAULT 'audio',
    mime_type TEXT,
    duration REAL,
    sample_rate INTEGER,
    channels INTEGER,
    parent_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    operations TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    status TEXT NOT NULL,
    text TEXT NOT NULL,
    model_type TEXT NOT NULL,
    checkpoint TEXT NOT NULL,
    voice_id TEXT REFERENCES voices(id) ON DELETE SET NULL,
    device TEXT NOT NULL,
    dtype TEXT,
    generation_config TEXT NOT NULL DEFAULT '{}',
    model_kwargs TEXT NOT NULL DEFAULT '{}',
    model_config TEXT NOT NULL DEFAULT '{}',
    optimization TEXT NOT NULL DEFAULT '{}',
    output_path TEXT,
    output_format TEXT NOT NULL DEFAULT 'wav',
    sample_rate INTEGER,
    duration REAL,
    latency REAL,
    metadata TEXT NOT NULL DEFAULT '{}',
    error TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    progress REAL NOT NULL DEFAULT 0,
    stage TEXT,
    payload TEXT NOT NULL DEFAULT '{}',
    result TEXT NOT NULL DEFAULT '{}',
    error TEXT,
    cancel_requested INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS training_runs (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    model_type TEXT NOT NULL,
    checkpoint TEXT NOT NULL,
    train_manifest TEXT NOT NULL,
    eval_manifest TEXT,
    output_dir TEXT NOT NULL,
    device TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    progress REAL NOT NULL DEFAULT 0,
    current_step INTEGER NOT NULL DEFAULT 0,
    total_steps INTEGER,
    training_loss REAL,
    error TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    sample_rate INTEGER NOT NULL DEFAULT 48000,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tracks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,
    gain_db REAL NOT NULL DEFAULT 0,
    muted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clips (
    id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE RESTRICT,
    position REAL NOT NULL DEFAULT 0,
    trim_in REAL NOT NULL DEFAULT 0,
    trim_out REAL,
    gain_db REAL NOT NULL DEFAULT 0,
    fade_in REAL NOT NULL DEFAULT 0,
    fade_out REAL NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_voices_updated ON voices(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_assets_created ON assets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generations_created ON generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_created ON training_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracks_project ON tracks(project_id, position);
CREATE INDEX IF NOT EXISTS idx_clips_track ON clips(track_id, position);
"""


class Database:
    """Thread-safe facade using short-lived SQLite connections."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = RLock()
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._write_lock:
            connection = self.connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def initialize(self) -> None:
        with self.transaction() as connection:
            connection.executescript(SCHEMA)
            existing = connection.execute(
                "SELECT version FROM schema_version LIMIT 1"
            ).fetchone()
            if existing is None:
                connection.execute("INSERT INTO schema_version(version) VALUES (1)")
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")

    def _insert(self, table: str, values: Mapping[str, Any]) -> dict[str, Any]:
        prepared = {
            key: _json(value)
            if key in JSON_COLUMNS and not isinstance(value, str)
            else value
            for key, value in values.items()
        }
        columns = ", ".join(prepared)
        placeholders = ", ".join("?" for _ in prepared)
        with self.transaction() as connection:
            connection.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(prepared.values()),
            )
        item = self.get(table, str(values["id"]))
        if item is None:
            raise RuntimeError(f"Failed to read inserted {table} record.")
        return item

    def get(self, table: str, record_id: str) -> dict[str, Any] | None:
        if table not in {
            "voices",
            "assets",
            "generations",
            "jobs",
            "training_runs",
            "projects",
            "tracks",
            "clips",
        }:
            raise ValueError("Unsupported table.")
        with self.connect() as connection:
            row = connection.execute(
                f"SELECT * FROM {table} WHERE id = ?", (record_id,)
            ).fetchone()
        return _decode_row(row)

    def list(
        self,
        table: str,
        *,
        limit: int = 100,
        offset: int = 0,
        where: str = "",
        parameters: Iterable[Any] = (),
    ) -> list[dict[str, Any]]:
        if table not in {
            "voices",
            "assets",
            "generations",
            "jobs",
            "training_runs",
            "projects",
            "tracks",
            "clips",
        }:
            raise ValueError("Unsupported table.")
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("Invalid pagination.")
        order_column = "updated_at" if table in {"voices", "projects"} else "created_at"
        if table in {"tracks", "clips"}:
            order_column = "position"
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        query += f" ORDER BY {order_column} DESC LIMIT ? OFFSET ?"
        with self.connect() as connection:
            rows = connection.execute(
                query, (*tuple(parameters), limit, offset)
            ).fetchall()
        return [_decode_row(row) or {} for row in rows]

    def update(
        self, table: str, record_id: str, values: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        if not values:
            return self.get(table, record_id)
        if table not in {
            "voices",
            "assets",
            "generations",
            "jobs",
            "training_runs",
            "projects",
            "tracks",
            "clips",
        }:
            raise ValueError("Unsupported table.")
        prepared = {
            key: _json(value)
            if key in JSON_COLUMNS and not isinstance(value, str)
            else value
            for key, value in values.items()
        }
        assignments = ", ".join(f"{key} = ?" for key in prepared)
        with self.transaction() as connection:
            connection.execute(
                f"UPDATE {table} SET {assignments} WHERE id = ?",
                (*tuple(prepared.values()), record_id),
            )
        return self.get(table, record_id)

    def delete(self, table: str, record_id: str) -> bool:
        if table not in {
            "voices",
            "assets",
            "generations",
            "training_runs",
            "projects",
            "tracks",
            "clips",
        }:
            raise ValueError("Unsupported table.")
        with self.transaction() as connection:
            cursor = connection.execute(
                f"DELETE FROM {table} WHERE id = ?", (record_id,)
            )
        return cursor.rowcount > 0

    def create_voice(self, values: Mapping[str, Any]) -> dict[str, Any]:
        now = utc_now()
        record = {
            "id": values.get("id") or new_id("voice"),
            "name": values["name"],
            "kind": values["kind"],
            "model_type": values.get("model_type"),
            "checkpoint": values.get("checkpoint"),
            "language": values.get("language"),
            "speaker": values.get("speaker"),
            "reference_asset_id": values.get("reference_asset_id"),
            "reference_text": values.get("reference_text"),
            "design_prompt": values.get("design_prompt"),
            "conditioning": values.get("conditioning", {}),
            "tags": values.get("tags", []),
            "favorite": int(bool(values.get("favorite", False))),
            "consent_confirmed": int(bool(values.get("consent_confirmed", False))),
            "consent_note": values.get("consent_note"),
            "source_uri": values.get("source_uri"),
            "created_at": now,
            "updated_at": now,
        }
        return self._insert("voices", record)

    def create_asset(self, values: Mapping[str, Any]) -> dict[str, Any]:
        record = {
            "id": values.get("id") or new_id("asset"),
            "name": values["name"],
            "path": str(values["path"]),
            "kind": values.get("kind", "audio"),
            "mime_type": values.get("mime_type"),
            "duration": values.get("duration"),
            "sample_rate": values.get("sample_rate"),
            "channels": values.get("channels"),
            "parent_id": values.get("parent_id"),
            "operations": values.get("operations", []),
            "metadata": values.get("metadata", {}),
            "created_at": utc_now(),
        }
        return self._insert("assets", record)

    def create_generation(self, values: Mapping[str, Any]) -> dict[str, Any]:
        record = {
            "id": values.get("id") or new_id("gen"),
            "job_id": values.get("job_id"),
            "status": values.get("status", "queued"),
            "text": values["text"],
            "model_type": values["model_type"],
            "checkpoint": values["checkpoint"],
            "voice_id": values.get("voice_id"),
            "device": values.get("device", "auto"),
            "dtype": values.get("dtype"),
            "generation_config": values.get("generation_config", {}),
            "model_kwargs": values.get("model_kwargs", {}),
            "model_config": values.get("model_config", {}),
            "optimization": values.get("optimization", {}),
            "output_path": values.get("output_path"),
            "output_format": values.get("output_format", "wav"),
            "sample_rate": values.get("sample_rate"),
            "duration": values.get("duration"),
            "latency": values.get("latency"),
            "metadata": values.get("metadata", {}),
            "error": values.get("error"),
            "created_at": utc_now(),
            "started_at": values.get("started_at"),
            "completed_at": values.get("completed_at"),
        }
        return self._insert("generations", record)

    def create_job(self, kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._insert(
            "jobs",
            {
                "id": new_id("job"),
                "kind": kind,
                "status": "queued",
                "progress": 0.0,
                "stage": "Waiting",
                "payload": dict(payload),
                "result": {},
                "error": None,
                "cancel_requested": 0,
                "created_at": utc_now(),
                "started_at": None,
                "completed_at": None,
            },
        )

    def create_training_run(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return self._insert(
            "training_runs",
            {
                "id": values.get("id") or new_id("train"),
                "job_id": values.get("job_id"),
                "name": values["name"],
                "status": values.get("status", "queued"),
                "model_type": values["model_type"],
                "checkpoint": values["checkpoint"],
                "train_manifest": values["train_manifest"],
                "eval_manifest": values.get("eval_manifest"),
                "output_dir": values["output_dir"],
                "device": values.get("device", "auto"),
                "config": values.get("config", {}),
                "progress": 0.0,
                "current_step": 0,
                "total_steps": values.get("total_steps"),
                "training_loss": None,
                "error": None,
                "created_at": utc_now(),
                "started_at": None,
                "completed_at": None,
            },
        )
