"""Load Section 1 outputs (facts, source pages) from disk or ingestion API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from analysis.settings import Settings


class IngestionNotReadyError(Exception):
    """Raised when Section 1 data is missing for a brand."""

    def __init__(self, brand_id: str, message: str) -> None:
        self.brand_id = brand_id
        super().__init__(message)


class IngestionClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def facts_path(self, brand_id: str) -> Path:
        return (
            self._settings.data_dir
            / "brands"
            / brand_id
            / "ingestion"
            / "normalized"
            / "facts.jsonl"
        )

    def source_pages_path(self, brand_id: str) -> Path:
        return (
            self._settings.data_dir
            / "brands"
            / brand_id
            / "ingestion"
            / "source_pages.jsonl"
        )

    def list_brands_with_facts(self) -> list[dict[str, Any]]:
        """Brands that have completed ingestion facts on disk."""
        root = self._settings.data_dir / "brands"
        if not root.exists():
            return []
        ready: list[dict[str, Any]] = []
        for brand_dir in root.iterdir():
            if not brand_dir.is_dir():
                continue
            brand_file = brand_dir / "brand.json"
            facts_file = self.facts_path(brand_dir.name)
            if brand_file.is_file() and facts_file.is_file():
                brand = json.loads(brand_file.read_text())
                fact_count = sum(1 for _ in facts_file.read_text().splitlines() if _.strip())
                ready.append(
                    {
                        "brand_id": brand_dir.name,
                        "name": brand.get("name"),
                        "primary_domain": brand.get("primary_domain"),
                        "fact_count": fact_count,
                    }
                )
        return sorted(ready, key=lambda b: b.get("name") or "")

    def load_facts(self, brand_id: str) -> list[dict[str, Any]]:
        local = self.facts_path(brand_id)
        if local.is_file():
            facts = _read_jsonl(local)
            if facts:
                return facts

        try:
            facts = self._fetch_facts_api(brand_id)
            if facts:
                return facts
        except httpx.HTTPError:
            pass

        raise IngestionNotReadyError(
            brand_id,
            _missing_facts_message(brand_id, local, self._settings.ingestion_api_url),
        )

    def load_source_pages(self, brand_id: str) -> list[dict[str, Any]]:
        local = self.source_pages_path(brand_id)
        if local.is_file():
            pages = _read_jsonl(local)
            if pages:
                return pages

        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.get(
                    f"{self._settings.ingestion_api_url}/brands/{brand_id}/source-pages"
                )
                r.raise_for_status()
                pages = r.json()
                if pages:
                    return pages
        except httpx.HTTPError:
            pass

        return []

    def check_ingestion_api(self) -> dict[str, Any]:
        url = f"{self._settings.ingestion_api_url}/health"
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url)
                r.raise_for_status()
                return {"ok": True, "url": self._settings.ingestion_api_url, **r.json()}
        except httpx.HTTPError as exc:
            return {"ok": False, "url": self._settings.ingestion_api_url, "error": str(exc)}

    def _fetch_facts_api(self, brand_id: str) -> list[dict[str, Any]]:
        with httpx.Client(timeout=60.0) as client:
            r = client.get(
                f"{self._settings.ingestion_api_url}/brands/{brand_id}/facts"
            )
            r.raise_for_status()
            return r.json()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _missing_facts_message(brand_id: str, local_path: Path, api_url: str) -> str:
    return (
        f"No ingestion facts for brand_id={brand_id}. "
        f"Run Section 1 first:\n"
        f"  python -m ingestion.cli ingest --name \"Your Brand\" --domain yourdomain.com\n"
        f"Then analyze with the brand_id from that output.\n"
        f"Expected file: {local_path}\n"
        f"Or start ingestion API ({api_url}) and ensure the brand exists."
    )
