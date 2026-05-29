"""Intent-specific prompt templates with rotating fact slots."""

from __future__ import annotations

from typing import Any

INTENT_BUCKETS = [
    "informational",
    "commercial_investigation",
    "transactional",
    "comparison",
    "problem_solution",
    "alternative_switching",
]

PERSONAS = ["evaluator", "buyer", "operator", "switcher"]

HIGH_INTENT = frozenset(
    {"transactional", "comparison", "alternative_switching"}
)

SLOT_FIELDS = (
    "features",
    "pain_points",
    "competitor_mentions",
    "products",
    "pricing_terms",
    "industries",
)


def build_fact_slots(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for fact in facts:
        slot: dict[str, Any] = {"normalized_fact_id": fact.get("normalized_fact_id", "")}
        for field in SLOT_FIELDS:
            values = fact.get(field) or []
            slot[field] = values[0] if values else None
        slots.append(slot)
    return slots or [_empty_slot()]


def render_template(
    intent: str,
    persona: str,
    slot: dict[str, Any],
) -> str:
    feat = slot.get("features") or "your product"
    pain = slot.get("pain_points") or "reporting gaps"
    comp = slot.get("competitor_mentions") or "incumbent tools"
    product = slot.get("products") or "analytics platform"
    pricing = slot.get("pricing_terms") or "flexible plans"
    industry = slot.get("industries") or "SaaS teams"

    templates = {
        "informational": (
            f"As a {persona} in {industry}, how does {feat} help with day-to-day reporting?"
        ),
        "commercial_investigation": (
            f"As a {persona}, what should I compare when evaluating {product} for {pain}?"
        ),
        "transactional": (
            f"As a {persona}, what's the fastest way to buy {product} with {pricing}?"
        ),
        "comparison": (
            f"As a {persona}, how does {feat} on {product} compare to {comp}?"
        ),
        "problem_solution": (
            f"As a {persona}, how do I fix {pain} without a long {product} implementation?"
        ),
        "alternative_switching": (
            f"As a {persona}, why switch from {comp} to {product} with {feat}?"
        ),
    }
    return templates.get(intent, "")


def _empty_slot() -> dict[str, Any]:
    return {field: None for field in SLOT_FIELDS}
