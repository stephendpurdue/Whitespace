"""End-to-end ingestion orchestration."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from ingestion.extract_runner import ExtractRunner
from ingestion.models import Brand, BrandInput, utc_now
from ingestion.normalization import NormalizationPipeline
from ingestion.settings import Settings
from ingestion.storage import BrandRepository
from ingestion.tavily_client import TavilyAPIError, TavilyClient


class IngestionPipeline:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._repo = BrandRepository(settings)
        self._client = TavilyClient(settings)
        self._extract = ExtractRunner(self._client)
        self._normalize = NormalizationPipeline()

    def run(
        self,
        brand_input: BrandInput,
        *,
        brand: Brand | None = None,
    ) -> dict[str, Any]:
        brand = brand or Brand.from_input(brand_input)
        batch_run_id = str(uuid4())
        started_at = utc_now()
        errors: list[dict[str, Any]] = []

        self._repo.save_brand(brand.to_dict())
        ing = self._repo.ingestion_dir(brand.brand_id)
        ing.mkdir(parents=True, exist_ok=True)

        batch_run = {
            "batch_run_id": batch_run_id,
            "brand_id": brand.brand_id,
            "run_type": "ingestion",
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "stats": {},
            "errors": errors,
        }
        self._repo.write_batch_run(ing, batch_run)

        raw_pages: list[dict[str, Any]] = []
        try:
            crawl = self._client.crawl(brand.primary_domain)
            raw_pages = merge_pages(crawl.get("pages", []))
            sparse_urls = [
                p["url"]
                for p in raw_pages
                if p.get("url") and not (p.get("raw_content") or "").strip()
            ]
            if sparse_urls:
                raw_pages = merge_pages(raw_pages + self._extract.run(sparse_urls))
        except TavilyAPIError as exc:
            errors.append(
                {
                    "code": "TAVILY_CRAWL_FAILED",
                    "message": str(exc),
                    "details": {"status_code": exc.status_code},
                }
            )

        raw_dir = ing / "raw"
        for page in raw_pages:
            content = page.get("raw_content", "")
            if content:
                page["raw_content_path"] = self._repo.save_raw_content(
                    raw_dir, page["url"], content
                )

        source_pages, facts = self._normalize.run(
            brand.brand_id,
            raw_pages,
            brand_name=brand.name,
            competitor_domains=brand.competitor_domains,
        )
        self._repo.write_jsonl(ing / "source_pages.jsonl", source_pages)
        self._repo.write_jsonl(ing / "normalized" / "facts.jsonl", facts)

        status = batch_status(errors, facts, raw_pages)
        batch_run.update(
            {
                "status": status,
                "finished_at": utc_now(),
                "stats": {
                    "source_pages": len(source_pages),
                    "normalized_facts": len(facts),
                    "raw_pages": len(raw_pages),
                },
                "errors": errors,
            }
        )
        self._repo.write_batch_run(ing, batch_run)

        return {
            "brand_id": brand.brand_id,
            "batch_run_id": batch_run_id,
            "status": status,
            "source_pages": len(source_pages),
            "normalized_facts": len(facts),
        }

    def close(self) -> None:
        self._client.close()


def merge_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge by URL; prefer longer raw_content."""
    by_url: dict[str, dict[str, Any]] = {}
    for page in pages:
        url = page.get("url", "")
        if not url:
            continue
        existing = by_url.get(url)
        if not existing or len(page.get("raw_content", "")) > len(
            existing.get("raw_content", "")
        ):
            by_url[url] = page
    return list(by_url.values())


def batch_status(
    errors: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    raw_pages: list[dict[str, Any]],
) -> str:
    if errors and not facts:
        return "failed"
    if errors or (raw_pages and not facts):
        return "partial"
    if facts:
        return "completed"
    return "partial"
