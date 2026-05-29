"""Pipeline integration and rescore tests."""

from __future__ import annotations

import json
from pathlib import Path

from analysis.pipeline import AnalysisPipeline


def test_analyze_fixture_brand(test_settings, seeded_brand: str):
    result = AnalysisPipeline(test_settings).run(seeded_brand)

    export_path = Path(result["export_path"])
    assert export_path.exists()
    export = json.loads(export_path.read_text())
    assert export["brand_id"] == seeded_brand
    assert len(export["triggers"]) > 0

    top = export["triggers"][0]
    assert top.get("prompt_run_ids")
    assert top.get("trigger_candidate_id")
    assert top.get("recommended_action") in (
        "prioritize",
        "test",
        "monitor",
        "deprioritize",
    )
    phrase_types = {t["phrase_type"] for t in export["triggers"]}
    assert phrase_types & {"unigram", "bigram", "keyphrase", "entity"}


def test_analyze_writes_batch_run(test_settings, seeded_brand: str):
    AnalysisPipeline(test_settings).run(seeded_brand)
    batch_path = (
        test_settings.data_dir
        / "brands"
        / seeded_brand
        / "analysis"
        / "batch_run.json"
    )
    batch = json.loads(batch_path.read_text())
    assert batch["run_type"] == "analysis"
    assert batch["status"] == "completed"
    assert batch["stats"]["prompts"] > 0


def test_rescore_updates_export(test_settings, seeded_brand: str):
    pipeline = AnalysisPipeline(test_settings)
    pipeline.run(seeded_brand)

    export_path = (
        test_settings.data_dir
        / "brands"
        / seeded_brand
        / "analysis"
        / "export"
        / "ranked_triggers.json"
    )
    before = json.loads(export_path.read_text())
    first_score = before["triggers"][0]["trigger_score"]

    result = pipeline.rescore(seeded_brand)
    after = json.loads(export_path.read_text())

    assert result["triggers"] == len(after["triggers"])
    assert after["triggers"][0]["trigger_score"] == first_score


def test_export_has_non_mixed_intent_for_focused_phrase(test_settings, seeded_brand: str):
    result = AnalysisPipeline(test_settings).run(seeded_brand)
    export = json.loads(Path(result["export_path"]).read_text())

    non_mixed = [t for t in export["triggers"] if t["intent_bucket"] != "mixed"]
    assert non_mixed, "expected at least one trigger with resolved intent"
