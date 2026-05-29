"""Tests for JSON schema validation."""

from __future__ import annotations

import pytest

from analysis.validation import validate_record


def test_validate_prompt_record(repo_root):
    prompt = {
        "prompt_id": "50000000-0000-4000-8000-000000000001",
        "brand_id": "00000000-0000-4000-8000-000000000001",
        "text": "How does funnel reporting work?",
        "intent_bucket": "informational",
        "persona": "evaluator",
        "is_high_intent": False,
        "seed_fact_ids": ["10000000-0000-4000-8000-000000000001"],
    }
    validate_record(prompt, "prompt.json", repo_root / "shared" / "schemas")


def test_validate_trigger_candidate_record(repo_root):
    trigger = {
        "trigger_candidate_id": "60000000-0000-4000-8000-000000000001",
        "brand_id": "00000000-0000-4000-8000-000000000001",
        "batch_run_id": "40000000-0000-4000-8000-000000000001",
        "phrase": "funnel reporting",
        "phrase_type": "bigram",
        "intent_bucket": "transactional",
        "trigger_score": 0.72,
        "recommended_action": "test",
        "appearance_count": 3,
        "appearance_rate": 0.25,
        "avg_rank_position": 1.5,
        "brand_proximity_score": 0.5,
        "commercial_intent_score": 1.0,
        "competitor_overlap_score": 0.0,
        "source_coverage": 0.2,
        "prompt_run_ids": ["70000000-0000-4000-8000-000000000001"],
        "source_page_ids": ["20000000-0000-4000-8000-000000000001"],
        "score_breakdown": {
            "frequency_score": 0.2,
            "intent_score": 0.25,
            "relevance_score": 0.15,
            "distinctiveness_score": 0.12,
            "ambiguity_penalty": 0.0,
        },
    }
    validate_record(trigger, "trigger_candidate.json", repo_root / "shared" / "schemas")


def test_validate_rejects_invalid_intent(repo_root):
    prompt = {
        "prompt_id": "50000000-0000-4000-8000-000000000001",
        "brand_id": "00000000-0000-4000-8000-000000000001",
        "text": "test",
        "intent_bucket": "not_a_real_bucket",
        "persona": "evaluator",
    }
    with pytest.raises(Exception):
        validate_record(prompt, "prompt.json", repo_root / "shared" / "schemas")
