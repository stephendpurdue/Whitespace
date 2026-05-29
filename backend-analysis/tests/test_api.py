"""Tests for analysis FastAPI endpoints."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from analysis.api.app import app
from analysis.export.ranked_export import write_ranked_export
from analysis.fixtures import SAMPLE_BRAND_ID


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from analysis.settings import reload_settings

    reload_settings()
    return TestClient(app)


def test_health(api_client: TestClient):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "analysis"}


def test_triggers_404_when_missing(api_client: TestClient):
    response = api_client.get(f"/brands/{SAMPLE_BRAND_ID}/triggers")
    assert response.status_code == 404


def test_prompt_runs_empty_when_missing(api_client: TestClient):
    response = api_client.get(f"/brands/{SAMPLE_BRAND_ID}/prompt-runs")
    assert response.status_code == 200
    assert response.json() == []


def test_batch_run_404_when_missing(api_client: TestClient):
    response = api_client.get(f"/brands/{SAMPLE_BRAND_ID}/batch-run")
    assert response.status_code == 404


def test_triggers_returns_export(api_client: TestClient, tmp_path):
    export_dir = (
        tmp_path / "brands" / SAMPLE_BRAND_ID / "analysis" / "export"
    )
    write_ranked_export(
        export_dir / "ranked_triggers.json",
        brand_id=SAMPLE_BRAND_ID,
        batch_run_id="40000000-0000-4000-8000-000000000001",
        scoring_config_version="1.0.0",
        triggers=[],
    )

    response = api_client.get(f"/brands/{SAMPLE_BRAND_ID}/triggers")
    assert response.status_code == 200
    assert response.json()["brand_id"] == SAMPLE_BRAND_ID


def test_batch_run_returns_metadata(api_client: TestClient, tmp_path):
    analysis_dir = tmp_path / "brands" / SAMPLE_BRAND_ID / "analysis"
    analysis_dir.mkdir(parents=True)
    batch = {
        "batch_run_id": "40000000-0000-4000-8000-000000000001",
        "brand_id": SAMPLE_BRAND_ID,
        "run_type": "analysis",
        "status": "completed",
        "started_at": "2026-05-28T12:00:00Z",
        "scoring_config_version": "1.0.0",
        "stats": {"prompts": 24, "triggers": 10},
        "errors": [],
    }
    (analysis_dir / "batch_run.json").write_text(json.dumps(batch))

    response = api_client.get(f"/brands/{SAMPLE_BRAND_ID}/batch-run")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_start_analysis_requires_facts(api_client: TestClient):
    response = api_client.post(f"/brands/{SAMPLE_BRAND_ID}/analyze")
    assert response.status_code == 400


def test_start_analysis_accepted(api_client: TestClient, tmp_path):
    from analysis.fixtures import seed_fixture_data

    seed_fixture_data(tmp_path)
    response = api_client.post(f"/brands/{SAMPLE_BRAND_ID}/analyze")
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def test_prompt_runs_reads_jsonl(api_client: TestClient, tmp_path):
    analysis_dir = tmp_path / "brands" / SAMPLE_BRAND_ID / "analysis"
    analysis_dir.mkdir(parents=True)
    run = {
        "prompt_run_id": "70000000-0000-4000-8000-000000000001",
        "prompt_id": "50000000-0000-4000-8000-000000000001",
        "brand_id": SAMPLE_BRAND_ID,
        "batch_run_id": "40000000-0000-4000-8000-000000000001",
        "status": "completed",
    }
    (analysis_dir / "prompt_runs.jsonl").write_text(json.dumps(run) + "\n")

    response = api_client.get(f"/brands/{SAMPLE_BRAND_ID}/prompt-runs")
    assert response.status_code == 200
    assert len(response.json()) == 1
