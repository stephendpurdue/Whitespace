"""Shared pytest fixtures for backend-analysis tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.fixtures import SAMPLE_BRAND_ID, seed_fixture_data
from analysis.settings import Settings, get_settings


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def test_settings(tmp_path: Path, repo_root: Path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        ingestion_api_url="http://127.0.0.1:8001",
        schemas_dir=repo_root / "shared" / "schemas",
        scoring_config_path=repo_root / "shared" / "config" / "scoring.default.json",
    )


@pytest.fixture
def sample_brand_id() -> str:
    return SAMPLE_BRAND_ID


@pytest.fixture
def seeded_brand(test_settings: Settings, sample_brand_id: str) -> str:
    seed_fixture_data(test_settings.data_dir)
    return sample_brand_id


@pytest.fixture
def sample_facts() -> list[dict]:
    return [
        {
            "normalized_fact_id": "10000000-0000-4000-8000-000000000001",
            "brand_id": SAMPLE_BRAND_ID,
            "source_page_id": "20000000-0000-4000-8000-000000000001",
            "title": "Funnel reporting",
            "summary": "Build conversion funnels and cohort retention for growth teams.",
            "features": ["funnel reporting", "cohort analysis"],
            "pain_points": ["broken conversion tracking"],
            "competitor_mentions": ["Rival Metrics"],
            "products": ["Acme Analytics Platform"],
            "brand_phrases": ["Acme Analytics"],
            "pricing_terms": ["free trial"],
            "industries": ["SaaS"],
        },
        {
            "normalized_fact_id": "10000000-0000-4000-8000-000000000002",
            "brand_id": SAMPLE_BRAND_ID,
            "source_page_id": "20000000-0000-4000-8000-000000000002",
            "title": "Pricing",
            "summary": "Per-seat pricing with enterprise SSO.",
            "features": ["SSO"],
            "pain_points": [],
            "competitor_mentions": ["Incumbent BI"],
            "products": ["Enterprise"],
            "brand_phrases": [],
            "pricing_terms": ["per-seat"],
            "industries": [],
        },
    ]


@pytest.fixture
def scoring_config(repo_root: Path) -> dict:
    return json.loads(
        (repo_root / "shared" / "config" / "scoring.default.json").read_text()
    )


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
