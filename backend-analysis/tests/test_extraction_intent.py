from analysis.extraction.intent_resolver import resolve_intent_bucket


def test_resolve_intent_bucket_mode():
    intents = ["transactional", "transactional", "commercial_investigation"]
    assert resolve_intent_bucket(intents) == "transactional"


def test_resolve_intent_bucket_mixed_when_no_majority():
    intents = [
        "informational",
        "transactional",
        "comparison",
        "problem_solution",
    ]
    assert resolve_intent_bucket(intents) == "mixed"


def test_resolve_intent_tiebreak_prefers_commercial():
    intents = ["informational", "comparison", "comparison"]
    assert resolve_intent_bucket(intents) == "comparison"


def test_transactional_beats_mixed_for_scoring_order(scoring_config: dict):
    from analysis.scoring.service import TriggerScoringService

    svc = TriggerScoringService(scoring_config)
    base = {
        "phrase_type": "bigram",
        "appearance_count": 5,
        "appearance_rate": 0.5,
        "source_page_ids": [],
    }
    transactional = svc.score([{**base, "phrase": "buy analytics now", "intent_bucket": "transactional"}])
    mixed = svc.score([{**base, "phrase": "buy analytics now", "intent_bucket": "mixed"}])
    assert transactional[0]["trigger_score"] > mixed[0]["trigger_score"]
