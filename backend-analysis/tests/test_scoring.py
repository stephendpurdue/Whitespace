"""Tests for TriggerScoringService."""

from __future__ import annotations

from analysis.scoring.service import TriggerScoringService, _action


def test_scoring_orders_by_trigger_score(scoring_config: dict):
    svc = TriggerScoringService(scoring_config)
    candidates = [
        {
            "phrase": "low",
            "phrase_type": "unigram",
            "appearance_count": 1,
            "appearance_rate": 0.1,
            "intent_bucket": "mixed",
            "source_page_ids": [],
        },
        {
            "phrase": "high intent phrase",
            "phrase_type": "bigram",
            "appearance_count": 10,
            "appearance_rate": 0.9,
            "intent_bucket": "transactional",
            "source_page_ids": ["a", "b"],
            "avg_rank_position": 1.5,
        },
    ]
    scored = svc.score(candidates)
    assert scored[0]["trigger_score"] >= scored[1]["trigger_score"]
    assert scored[0]["competitor_overlap_score"] >= 0
    assert scored[0]["brand_proximity_score"] >= 0
    assert scored[0]["avg_rank_position"] > 0


def test_competitor_overlap_from_facts(scoring_config: dict, sample_facts: list[dict]):
    svc = TriggerScoringService(scoring_config, sample_facts)
    candidates = [
        {
            "phrase": "rival metrics alternative",
            "phrase_type": "keyphrase",
            "appearance_count": 5,
            "appearance_rate": 0.5,
            "intent_bucket": "comparison",
            "source_page_ids": [],
        }
    ]
    scored = svc.score(candidates)
    assert scored[0]["competitor_overlap_score"] > 0


def test_brand_proximity_from_facts(scoring_config: dict, sample_facts: list[dict]):
    svc = TriggerScoringService(scoring_config, sample_facts)
    candidates = [
        {
            "phrase": "funnel reporting",
            "phrase_type": "bigram",
            "appearance_count": 5,
            "appearance_rate": 0.5,
            "intent_bucket": "informational",
            "source_page_ids": [],
        }
    ]
    scored = svc.score(candidates)
    assert scored[0]["brand_proximity_score"] > 0


def test_recommended_action_thresholds(scoring_config: dict):
    thresholds = scoring_config["thresholds"]
    assert _action(thresholds["prioritize"], thresholds) == "prioritize"
    assert _action(thresholds["test"], thresholds) == "test"
    assert _action(thresholds["monitor"], thresholds) == "monitor"
    assert _action(0.1, thresholds) == "deprioritize"


def test_entity_scores_higher_distinctiveness(scoring_config: dict):
    svc = TriggerScoringService(scoring_config)
    base = {
        "appearance_count": 5,
        "appearance_rate": 0.5,
        "intent_bucket": "informational",
        "source_page_ids": [],
        "phrase": "analytics",
    }
    entity = svc.score([{**base, "phrase_type": "entity"}])
    unigram = svc.score([{**base, "phrase_type": "unigram"}])
    assert entity[0]["score_breakdown"]["distinctiveness_score"] >= unigram[0]["score_breakdown"]["distinctiveness_score"]
