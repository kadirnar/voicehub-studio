from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient


def upload_tone(client: TestClient, tone_file: Path) -> dict:
    with tone_file.open("rb") as source:
        response = client.post(
            "/api/assets",
            files={"file": ("tone.wav", source, "audio/wav")},
            data={"name": "Test tone", "kind": "reference"},
        )
    assert response.status_code == 201, response.text
    return response.json()


def wait_for_job(client: TestClient, job_id: str, timeout: float = 5) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] not in {"queued", "running"}:
            return job
        time.sleep(0.03)
    raise AssertionError(f"Job {job_id} did not finish within {timeout:g} seconds")


def test_health_catalog_and_spa(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    catalog = client.get("/api/models").json()
    assert catalog["count"] >= 34
    qwen = client.get("/api/models/qwen3tts")
    assert qwen.status_code == 200
    assert qwen.json()["model"]["can_clone"] is True
    assert qwen.json()["advanced_json"] is True

    index = client.get("/")
    assert index.status_code == 200
    assert "VoiceHub Studio" in index.text
    assert client.get("/voices").status_code == 200


def test_voice_consent_and_profile_crud(client: TestClient, tone_file: Path) -> None:
    asset = upload_tone(client, tone_file)
    rejected = client.post(
        "/api/voices",
        json={
            "name": "Unauthorized",
            "kind": "clone",
            "reference_asset_id": asset["id"],
        },
    )
    assert rejected.status_code == 422

    created = client.post(
        "/api/voices",
        json={
            "name": "Authorized reference",
            "kind": "clone",
            "reference_asset_id": asset["id"],
            "reference_text": "A test reference.",
            "consent_confirmed": True,
            "tags": ["test", "narration"],
        },
    )
    assert created.status_code == 201, created.text
    voice = created.json()
    assert voice["consent_confirmed"] is True

    updated = client.patch(f"/api/voices/{voice['id']}", json={"favorite": True})
    assert updated.status_code == 200
    assert updated.json()["favorite"] is True
    assert client.delete(f"/api/voices/{voice['id']}").status_code == 204


def test_audio_waveform_and_background_edit(
    client: TestClient, tone_file: Path
) -> None:
    asset = upload_tone(client, tone_file)
    waveform = client.get(
        f"/api/assets/{asset['id']}/waveform", params={"buckets": 128}
    )
    assert waveform.status_code == 200
    assert waveform.json()["peaks"]

    response = client.post(
        "/api/audio/edit",
        json={
            "source_asset_id": asset["id"],
            "name": "Processed tone",
            "operations": [
                {"op": "gain", "db": -3},
                {"op": "fade_in", "duration": 0.1},
                {"op": "compress", "threshold_db": -18, "ratio": 2},
            ],
            "output_format": "wav",
        },
    )
    assert response.status_code == 202, response.text
    job = wait_for_job(client, response.json()["id"])
    assert job["status"] == "completed", job
    assert client.get("/api/assets").json()["count"] == 2


def test_projects_and_setting_validation(client: TestClient) -> None:
    created = client.post(
        "/api/projects", json={"name": "Episode one", "sample_rate": 48_000}
    )
    assert created.status_code == 201
    assert client.get("/api/projects").json()["count"] == 1

    settings = client.put(
        "/api/settings",
        json={"default_device": "cpu", "output_format": "flac", "queue_workers": 2},
    )
    assert settings.status_code == 200
    assert settings.json()["output_format"] == "flac"
    turkish = client.put("/api/settings", json={"interface_language": "tr"})
    assert turkish.status_code == 200
    assert turkish.json()["interface_language"] == "tr"
    assert (
        client.put("/api/settings", json={"interface_language": "xx"}).status_code
        == 400
    )
    assert client.put("/api/settings", json={"unknown_value": True}).status_code == 400
