"""Entity extraction from facts and response text."""

from __future__ import annotations

import re
from typing import Any

from analysis.extraction.provenance import PhraseProvenance, normalise_phrase

CAPITALISED_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
ENTITY_LIST_FIELDS = ("competitor_mentions", "products", "brand_phrases", "customer_types")


def known_entities_from_facts(facts: list[dict[str, Any]]) -> set[str]:
    entities: set[str] = set()
    for fact in facts:
        for field in ENTITY_LIST_FIELDS:
            for value in fact.get(field) or []:
                entities.add(normalise_phrase(str(value)))
    return entities


def extract_entities(
    prompt_runs: list[dict[str, Any]],
    fragments_by_run: dict[str, list[dict[str, Any]]],
    facts: list[dict[str, Any]],
) -> dict[str, PhraseProvenance]:
    known = known_entities_from_facts(facts)
    provenance: dict[str, PhraseProvenance] = {}

    for run in prompt_runs:
        run_id = run["prompt_run_id"]
        frags = fragments_by_run.get(run_id, [])
        source_ids = [f.get("source_page_id", "") for f in frags if f.get("source_page_id")]
        ranks = [float(f.get("rank_position", 0)) for f in frags if f.get("rank_position")]
        text = run.get("response_text") or ""
        text_lower = text.lower()

        found: set[str] = {e for e in known if e in text_lower}
        for match in CAPITALISED_RE.findall(text):
            found.add(normalise_phrase(match))

        for entity in found:
            if entity not in provenance:
                provenance[entity] = PhraseProvenance(phrase=entity, phrase_type="entity")
            provenance[entity].record(
                prompt_run_id=run_id,
                source_page_ids=source_ids,
                rank_positions=ranks,
            )

    return provenance
