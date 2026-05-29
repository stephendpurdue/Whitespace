"""Tests for ranked trigger export."""

from __future__ import annotations

import json
from pathlib import Path

from analysis.export.ranked_export import write_ranked_export


def test_write_ranked_export_shape(tmp_path: Path):
    triggers = [
        {
            "trigger_candidate_id": "30000000-0000-4000-8000-000000000001",
            "phrase": "funnel reporting",
            "phrase_type": "bigram",
            "trigger_score": 0.8,
            "intent_bucket": "transactional",
            "recommended_action": "test",
        }
    ]
    path = tmp_path / "export" / "ranked_triggers.json"
    write_ranked_export(
        path,
        brand_id="00000000-0000-4000-8000-000000000001",
        batch_run_id="40000000-0000-4000-8000-000000000001",
        scoring_config_version="1.0.0",
        triggers=triggers,
    )

    payload = json.loads(path.read_text())
    assert payload["brand_id"] == "00000000-0000-4000-8000-000000000001"
    assert payload["batch_run_id"] == "40000000-0000-4000-8000-000000000001"
    assert payload["scoring_config_version"] == "1.0.0"
    assert payload["generated_at"]
    assert len(payload["triggers"]) == 1
    assert payload["triggers"][0]["phrase"] == "funnel reporting"
