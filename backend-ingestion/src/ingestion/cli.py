"""CLI entrypoint for brand ingestion jobs."""

from __future__ import annotations

import json
from typing import Optional

import typer

from ingestion.models import BrandInput
from ingestion.pipeline import IngestionPipeline
from ingestion.settings import BACKEND_ROOT, get_settings, reload_settings
from ingestion.tavily_client import TavilyAPIError, TavilyClient

app = typer.Typer(help="Brand ingestion (Tavily crawl/extract/normalize)")


def _config_report() -> dict:
    reload_settings()
    settings = get_settings()
    env_file = BACKEND_ROOT / ".env"
    return {
        "env_file": str(env_file),
        "env_file_exists": env_file.is_file(),
        "api_key_configured": bool(settings.tavily_api_key),
        "mock_mode": settings.tavily_mock,
        "data_dir": str(settings.data_dir),
    }


@app.command()
def test(
    live: bool = typer.Option(
        False,
        "--live",
        help="Call Tavily Extract on one URL (uses API credits).",
    ),
) -> None:
    """Verify setup; use --live to confirm the API key works against Tavily."""
    settings = get_settings()
    report: dict = {"ok": True, **_config_report(), "live_test": None}

    if not report["env_file_exists"]:
        report["ok"] = False
        report["error"] = f"Missing {report['env_file']} — copy .env.example to .env"
    elif not report["api_key_configured"]:
        report["ok"] = False
        report["error"] = "TAVILY_API_KEY is empty in .env"
    elif report["mock_mode"] and live:
        report["ok"] = False
        report["error"] = "mock_mode is on — set TAVILY_API_KEY or set TAVILY_MOCK=false"

    if live and report["ok"]:
        client = TavilyClient(settings)
        try:
            pages = client.extract(["https://docs.tavily.com"])
            report["live_test"] = {
                "status": "ok" if pages else "empty_response",
                "pages_returned": len(pages),
                "sample_url": pages[0]["url"] if pages else None,
            }
            if not pages:
                report["ok"] = False
        except TavilyAPIError as exc:
            report["ok"] = False
            report["live_test"] = {"status": "error", "message": str(exc)}
        finally:
            client.close()

    typer.echo(json.dumps(report, indent=2))
    if not report["ok"]:
        raise typer.Exit(code=1)


@app.command()
def ingest(
    name: str = typer.Option(..., help="Brand display name"),
    domain: str = typer.Option(..., help="Primary domain, e.g. acme.com"),
    competitors: Optional[str] = typer.Option(
        None, help="Comma-separated competitor domains"
    ),
    topics: Optional[str] = typer.Option(None, help="Comma-separated seed topics"),
) -> None:
    """Run full ingestion: crawl, extract, normalize, persist."""
    reload_settings()
    pipeline = IngestionPipeline(get_settings())
    try:
        result = pipeline.run(
            BrandInput(
                name=name,
                primary_domain=domain,
                competitor_domains=_split(competitors),
                seed_topics=_split(topics),
            )
        )
    finally:
        pipeline.close()
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8001) -> None:
    """Start local knowledge-base API."""
    import uvicorn

    uvicorn.run("ingestion.api.app:app", host=host, port=port, reload=True)


def _split(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


if __name__ == "__main__":
    app()
