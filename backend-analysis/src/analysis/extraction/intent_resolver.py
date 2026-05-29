"""Resolve dominant intent bucket for a trigger phrase."""

from __future__ import annotations

from collections import Counter

COMMERCIAL_ORDER = (
    "transactional",
    "comparison",
    "alternative_switching",
    "commercial_investigation",
    "problem_solution",
    "informational",
)


def resolve_intent_bucket(
    intents: list[str],
    *,
    mixed_threshold: float = 0.4,
) -> str:
    if not intents:
        return "mixed"
    counts = Counter(intents)
    if len(counts) >= 3:
        top_count = counts.most_common(1)[0][1]
        if top_count / len(intents) < mixed_threshold:
            return "mixed"
    mode_count = counts.most_common(1)[0][1]
    modes = [k for k, v in counts.items() if v == mode_count]
    if len(modes) == 1:
        return modes[0]
    for bucket in COMMERCIAL_ORDER:
        if bucket in modes:
            return bucket
    return modes[0]
