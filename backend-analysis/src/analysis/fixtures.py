"""Copy shared fixture data into the local data directory."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SAMPLE_BRAND_ID = "00000000-0000-4000-8000-000000000001"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def seed_fixture_data(data_dir: Path) -> dict[str, str]:
    root = repo_root()
    fixtures = root / "shared" / "fixtures"
    brand_dir = data_dir / "brands" / SAMPLE_BRAND_ID
    brand_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(fixtures / "sample_brand.json", brand_dir / "brand.json")
    normalised = brand_dir / "ingestion" / "normalized"
    normalised.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixtures / "sample_facts.jsonl", normalised / "facts.jsonl")

    return {
        "brand_id": SAMPLE_BRAND_ID,
        "brand_json": str(brand_dir / "brand.json"),
        "facts_jsonl": str(normalised / "facts.jsonl"),
    }
