"""Weighted trigger scoring per shared/config/scoring.default.json."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

COMMERCIAL_INTENT_SCORES = {
    "transactional": 1.0,
    "comparison": 0.9,
    "alternative_switching": 0.85,
    "commercial_investigation": 0.75,
    "problem_solution": 0.65,
    "informational": 0.5,
    "mixed": 0.4,
}


class TriggerScoringService:
    def __init__(self, config: dict[str, Any], facts: list[dict[str, Any]] | None = None) -> None:
        self._config = config
        self._competitors = _collect_terms(facts or [], "competitor_mentions")
        self._brand_terms = _collect_terms(facts or [], "brand_phrases") | _collect_terms(
            facts or [], "features"
        )

    def score(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        weights = self._config.get("weights", {})
        thresholds = self._config.get("thresholds", {})
        scored: list[dict[str, Any]] = []

        max_count = max((c["appearance_count"] for c in candidates), default=1)

        for c in candidates:
            frequency_score = (c["appearance_count"] / max_count) * weights.get(
                "frequency", 0.3
            )
            bucket = c.get("intent_bucket", "mixed")
            intent_multiplier = COMMERCIAL_INTENT_SCORES.get(bucket, 0.4)
            intent_score = weights.get("intent", 0.25) * intent_multiplier
            relevance_score = weights.get("relevance", 0.25) * min(
                1.0, c.get("appearance_rate", 0) * 2
            )
            distinctiveness_score = weights.get("distinctiveness", 0.15) * (
                _distinctiveness(c.get("phrase_type", "unigram"))
            )
            ambiguity_penalty = weights.get("ambiguity_penalty", 0.05) * (
                1.0 if len(c["phrase"]) < 5 else 0.0
            )
            trigger_score = (
                frequency_score
                + intent_score
                + relevance_score
                + distinctiveness_score
                - ambiguity_penalty
            )
            brand_proximity = _term_overlap(c["phrase"], self._brand_terms)
            competitor_overlap = _term_overlap(c["phrase"], self._competitors)
            avg_rank = c.get("avg_rank_position")
            if avg_rank is None:
                avg_rank = 2.5

            c = {
                **c,
                "trigger_candidate_id": str(uuid4()),
                "trigger_score": round(trigger_score, 4),
                "avg_rank_position": round(avg_rank, 2),
                "brand_proximity_score": round(brand_proximity, 4),
                "commercial_intent_score": round(intent_multiplier, 4),
                "competitor_overlap_score": round(competitor_overlap, 4),
                "source_coverage": min(1.0, len(c.get("source_page_ids", [])) / 10),
                "recommended_action": _action(trigger_score, thresholds),
                "score_breakdown": {
                    "frequency_score": frequency_score,
                    "intent_score": intent_score,
                    "relevance_score": relevance_score,
                    "distinctiveness_score": distinctiveness_score,
                    "ambiguity_penalty": ambiguity_penalty,
                },
            }
            scored.append(c)

        scored.sort(key=lambda x: x["trigger_score"], reverse=True)
        return scored


def _distinctiveness(phrase_type: str) -> float:
    return {
        "entity": 1.0,
        "keyphrase": 0.95,
        "bigram": 0.85,
        "unigram": 0.6,
    }.get(phrase_type, 0.6)


def _collect_terms(facts: list[dict[str, Any]], field: str) -> set[str]:
    terms: set[str] = set()
    for fact in facts:
        for value in fact.get(field) or []:
            terms.add(value.lower())
    return terms


def _term_overlap(phrase: str, terms: set[str]) -> float:
    if not terms:
        return 0.0
    phrase_tokens = set(phrase.lower().split())
    if not phrase_tokens:
        return 0.0
    hits = sum(1 for t in terms if t in phrase.lower() or t in phrase_tokens)
    return min(1.0, hits / max(len(phrase_tokens), 1))


def _action(score: float, thresholds: dict[str, float]) -> str:
    if score >= thresholds.get("prioritize", 0.75):
        return "prioritize"
    if score >= thresholds.get("test", 0.55):
        return "test"
    if score >= thresholds.get("monitor", 0.35):
        return "monitor"
    return "deprioritize"
