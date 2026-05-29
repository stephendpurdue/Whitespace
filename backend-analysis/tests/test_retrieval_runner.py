"""Tests for RetrievalRunner and corpus helpers."""

from __future__ import annotations

import pytest

from analysis.retrieval.corpus_index import fact_to_document, tokenise
from analysis.retrieval.runner import RetrievalRunner


def test_fact_to_document_includes_list_fields():
    fact = {
        "title": "Home",
        "summary": "Analytics platform",
        "features": ["funnels", "cohorts"],
        "pain_points": ["slow reports"],
    }
    doc = fact_to_document(fact)
    assert "funnels" in doc
    assert "slow reports" in doc


def test_tokenise_lowercases_and_filters_short_tokens():
    tokens = tokenise("Funnel Reporting 2024 for teams")
    assert "funnel" in tokens
    assert "reporting" in tokens
    assert "2024" in tokens


def test_retrieval_runner_returns_fragments(sample_facts: list[dict]):
    runner = RetrievalRunner(sample_facts)
    prompt = {
        "prompt_id": "p1",
        "brand_id": "b1",
        "text": "How does funnel reporting compare to rivals?",
    }
    run = runner.run_prompt(prompt)

    assert run["status"] == "completed"
    assert run["prompt_id"] == "p1"
    assert run["response_text"]
    assert len(run["fragments"]) <= 5
    assert run["fragments"][0]["rank_position"] == 1
    assert run["fragments"][0]["snippet_score"] > 0


def test_retrieval_runner_links_source_pages(sample_facts: list[dict]):
    runner = RetrievalRunner(sample_facts)
    prompt = {
        "prompt_id": "p1",
        "brand_id": "b1",
        "text": "funnel reporting cohort analysis",
    }
    run = runner.run_prompt(prompt)

    assert run["source_page_ids"]
    assert all(
        fid.get("source_page_id") in run["source_page_ids"]
        for fid in run["fragments"]
        if fid.get("source_page_id")
    )


@pytest.mark.parametrize("mode", ["bm25"])
def test_retrieval_respects_mode_env(sample_facts: list[dict], mode: str, monkeypatch):
    monkeypatch.setenv("RETRIEVAL_MODE", mode)
    runner = RetrievalRunner(sample_facts)
    prompt = {"prompt_id": "p1", "brand_id": "b1", "text": "enterprise pricing SSO"}
    run = runner.run_prompt(prompt)
    assert run["fragments"]
