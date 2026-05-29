"""CLI for analysis batch jobs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from analysis.fixtures import SAMPLE_BRAND_ID, seed_fixture_data
from analysis.ingestion_client import IngestionClient, IngestionNotReadyError
from analysis.pipeline import AnalysisPipeline
from analysis.settings import REPO_ROOT, get_settings, reload_settings

app = typer.Typer(help="Trigger analysis (prompts, retrieval, scoring)")


@app.command()
def test(
    brand_id: Optional[str] = typer.Option(
        None, "--brand-id", help="Verify facts exist for this brand"
    ),
) -> None:
    """Verify Section 2 can read Section 1 data (shared data dir + optional API)."""
    reload_settings()
    settings = get_settings()
    client = IngestionClient(settings)

    report: dict = {
        "ok": True,
        "data_dir": str(settings.data_dir),
        "ingestion_api_url": settings.ingestion_api_url,
        "ingestion_api": client.check_ingestion_api(),
        "brands_with_facts": client.list_brands_with_facts(),
    }

    if brand_id:
        try:
            facts = client.load_facts(brand_id)
            report["brand_id"] = brand_id
            report["fact_count"] = len(facts)
            report["source_page_count"] = len(client.load_source_pages(brand_id))
        except IngestionNotReadyError as exc:
            report["ok"] = False
            report["error"] = str(exc)
    elif not report["brands_with_facts"]:
        report["ok"] = False
        report["error"] = (
            "No ingested brands found. Run Section 1 ingest first, or use --brand-id."
        )

    typer.echo(json.dumps(report, indent=2, default=str))
    if not report["ok"]:
        raise typer.Exit(code=1)


@app.command("list-brands")
def list_brands() -> None:
    """List brands ready for analysis (have ingestion facts)."""
    reload_settings()
    brands = IngestionClient(get_settings()).list_brands_with_facts()
    typer.echo(json.dumps(brands, indent=2))
    if not brands:
        typer.echo(
            "No brands with facts. Run: python -m ingestion.cli ingest ...",
            err=True,
        )
        raise typer.Exit(code=1)


@app.command("generate-prompts")
def generate_prompts(brand_id: str = typer.Option(..., "--brand-id")) -> None:
    reload_settings()
    try:
        count = AnalysisPipeline(get_settings()).generate_prompts_only(brand_id)
    except IngestionNotReadyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Generated {count} prompts for {brand_id}")


@app.command()
def analyze(brand_id: str = typer.Option(..., "--brand-id")) -> None:
    reload_settings()
    try:
        result = AnalysisPipeline(get_settings()).run(brand_id)
    except IngestionNotReadyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def score(brand_id: str = typer.Option(..., "--brand-id")) -> None:
    reload_settings()
    try:
        result = AnalysisPipeline(get_settings()).rescore(brand_id)
    except IngestionNotReadyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command("run-pipeline")
def run_pipeline(
    name: str = typer.Option(..., help="Brand display name"),
    domain: str = typer.Option(..., help="Primary domain"),
    competitors: Optional[str] = typer.Option(None, help="Comma-separated domains"),
    topics: Optional[str] = typer.Option(None, help="Comma-separated seed topics"),
    skip_ingest: bool = typer.Option(
        False, "--skip-ingest", help="Only run analysis (brand must exist)"
    ),
    brand_id: Optional[str] = typer.Option(
        None, "--brand-id", help="Required with --skip-ingest"
    ),
) -> None:
    """Run Section 1 ingest then Section 2 analyze in one command."""
    if skip_ingest:
        if not brand_id:
            typer.echo("--brand-id is required when using --skip-ingest", err=True)
            raise typer.Exit(code=1)
    else:
        ingest_py = REPO_ROOT / "backend-ingestion" / ".venv" / "bin" / "python"
        if not ingest_py.is_file():
            ingest_py = Path(sys.executable)
        cmd = [
            str(ingest_py),
            "-m",
            "ingestion.cli",
            "ingest",
            "--name",
            name,
            "--domain",
            domain,
        ]
        if competitors:
            cmd.extend(["--competitors", competitors])
        if topics:
            cmd.extend(["--topics", topics])
        typer.echo("Running ingestion…", err=True)
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT / "backend-ingestion"),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            typer.echo(proc.stderr or proc.stdout, err=True)
            raise typer.Exit(proc.returncode)
        result = json.loads(proc.stdout)
        brand_id = result["brand_id"]
        typer.echo(json.dumps({"ingestion": result}, indent=2))

    assert brand_id
    reload_settings()
    typer.echo(f"Running analysis for {brand_id}…", err=True)
    try:
        analysis_result = AnalysisPipeline(get_settings()).run(brand_id)
    except IngestionNotReadyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps({"brand_id": brand_id, "analysis": analysis_result}, indent=2))


@app.command("seed-fixture")
def seed_fixture() -> None:
    reload_settings()
    paths = seed_fixture_data(get_settings().data_dir)
    typer.echo(json.dumps(paths, indent=2))
    typer.echo(f"Run: python -m analysis.cli analyze --brand-id {SAMPLE_BRAND_ID}")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8002) -> None:
    import uvicorn

    reload_settings()
    uvicorn.run("analysis.api.app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
