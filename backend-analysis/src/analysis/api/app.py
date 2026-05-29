from __future__ import annotations

import json
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from analysis.ingestion_client import IngestionClient, IngestionNotReadyError
from analysis.models import utc_now
from analysis.pipeline import AnalysisPipeline
from analysis.settings import get_settings

app = FastAPI(title="Trigger Discovery — Analysis API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _analysis_dir(brand_id: str) -> Path:
    return get_settings().data_dir / "brands" / brand_id / "analysis"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analysis"}


@app.get("/brands/{brand_id}/triggers")
def get_triggers(brand_id: str) -> dict:
    export = _analysis_dir(brand_id) / "export" / "ranked_triggers.json"
    if not export.exists():
        raise HTTPException(404, "No analysis export for brand")
    return json.loads(export.read_text())


@app.get("/brands/{brand_id}/prompt-runs")
def get_prompt_runs(brand_id: str) -> list[dict]:
    path = _analysis_dir(brand_id) / "prompt_runs.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@app.get("/brands/{brand_id}/batch-run")
def get_batch_run(brand_id: str) -> dict:
    path = _analysis_dir(brand_id) / "batch_run.json"
    if not path.exists():
        raise HTTPException(404, "No analysis batch run for brand")
    return json.loads(path.read_text())


def _run_analysis_job(brand_id: str) -> None:
    AnalysisPipeline(get_settings()).run(brand_id)


@app.post("/brands/{brand_id}/analyze", status_code=202)
def start_analysis(brand_id: str, background_tasks: BackgroundTasks) -> dict:
    """Start Section 2 analysis for a brand that has ingestion facts."""
    settings = get_settings()
    try:
        IngestionClient(settings).load_facts(brand_id)
    except IngestionNotReadyError as exc:
        raise HTTPException(400, str(exc)) from exc

    adir = _analysis_dir(brand_id)
    adir.mkdir(parents=True, exist_ok=True)
    pending = {
        "batch_run_id": "pending",
        "brand_id": brand_id,
        "run_type": "analysis",
        "status": "running",
        "started_at": utc_now(),
        "errors": [],
    }
    (adir / "batch_run.json").write_text(json.dumps(pending, indent=2))
    background_tasks.add_task(_run_analysis_job, brand_id)
    return {
        "brand_id": brand_id,
        "status": "accepted",
        "poll": f"/brands/{brand_id}/batch-run",
    }
