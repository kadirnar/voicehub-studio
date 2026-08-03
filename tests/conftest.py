from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from voicehub_studio.app import create_app
from voicehub_studio.config import AppPaths


@pytest.fixture
def app_paths(tmp_path: Path) -> AppPaths:
    return AppPaths(
        data=tmp_path,
        config=tmp_path / "config",
        cache=tmp_path / "cache",
        database=tmp_path / "studio.sqlite3",
        voices=tmp_path / "voices",
        assets=tmp_path / "assets",
        generations=tmp_path / "generations",
        training=tmp_path / "training",
        logs=tmp_path / "logs",
    )


@pytest.fixture
def client(app_paths: AppPaths) -> Iterator[TestClient]:
    with TestClient(create_app(app_paths)) as test_client:
        yield test_client


@pytest.fixture
def tone_file(tmp_path: Path) -> Path:
    if shutil.which("ffmpeg") is None:
        pytest.skip("FFmpeg is required for audio integration tests.")
    destination = tmp_path / "tone.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1.2",
            "-ar",
            "24000",
            "-ac",
            "1",
            str(destination),
        ],
        check=True,
    )
    return destination
