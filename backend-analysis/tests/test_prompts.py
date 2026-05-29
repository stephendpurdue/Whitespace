"""Tests for prompt generation and templates."""

from __future__ import annotations

from analysis.prompts.generator import PromptGenerator
from analysis.prompts.templates import INTENT_BUCKETS, PERSONAS, build_fact_slots, render_template


def test_build_fact_slots_includes_seed_ids(sample_facts: list[dict]):
    slots = build_fact_slots(sample_facts)
    assert len(slots) == len(sample_facts)
    assert slots[0]["normalized_fact_id"] == sample_facts[0]["normalized_fact_id"]
    assert slots[0]["features"] == "funnel reporting"


def test_render_template_uses_fact_values():
    slot = {
        "features": "cohort analysis",
        "pain_points": "slow reporting",
        "competitor_mentions": "Rival Metrics",
        "products": "Acme Platform",
        "pricing_terms": "free trial",
        "industries": "SaaS",
    }
    text = render_template("comparison", "buyer", slot)
    assert "cohort analysis" in text
    assert "Rival Metrics" in text


def test_prompt_generator_covers_intents_and_personas(sample_facts: list[dict]):
    brand_id = "00000000-0000-4000-8000-000000000001"
    prompts = PromptGenerator().generate(brand_id, sample_facts)

    assert len(prompts) == len(INTENT_BUCKETS) * len(PERSONAS)
    intents = {p["intent_bucket"] for p in prompts}
    personas = {p["persona"] for p in prompts}
    assert intents == set(INTENT_BUCKETS)


def test_prompt_generator_sets_seed_fact_ids(sample_facts: list[dict]):
    brand_id = "00000000-0000-4000-8000-000000000001"
    prompts = PromptGenerator().generate(brand_id, sample_facts)

    with_seeds = [p for p in prompts if p["seed_fact_ids"]]
    assert with_seeds
    for prompt in with_seeds:
        assert prompt["seed_fact_ids"][0] in {
            f["normalized_fact_id"] for f in sample_facts
        }


def test_high_intent_flags(sample_facts: list[dict]):
    brand_id = "00000000-0000-4000-8000-000000000001"
    prompts = PromptGenerator().generate(brand_id, sample_facts)

    transactional = [p for p in prompts if p["intent_bucket"] == "transactional"]
    assert transactional
    assert all(p["is_high_intent"] for p in transactional)

    informational = [p for p in prompts if p["intent_bucket"] == "informational"]
    assert all(not p["is_high_intent"] for p in informational)
