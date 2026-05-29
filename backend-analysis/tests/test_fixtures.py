"""Tests for fixture seeding."""

from __future__ import annotations

import json

from analysis.fixtures import SAMPLE_BRAND_ID, seed_fixture_data


def test_seed_fixture_data_writes_brand_and_facts(tmp_path):
    paths = seed_fixture_data(tmp_path)

    assert paths["brand_id"] == SAMPLE_BRAND_ID
    brand = json.loads((tmp_path / "brands" / SAMPLE_BRAND_ID / "brand.json").read_text())
    assert brand["name"] == "Acme Analytics"

    facts_path = tmp_path / "brands" / SAMPLE_BRAND_ID / "ingestion" / "normalized" / "facts.jsonl"
    lines = [line for line in facts_path.read_text().splitlines() if line.strip()]
    assert len(lines) >= 5
