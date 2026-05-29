"""Orchestrate phrase, keyphrase, and entity extraction."""

from __future__ import annotations

from typing import Any

from analysis.extraction.candidate_merger import merge_provenance_maps, to_candidates
from analysis.extraction.entity_extractor import extract_entities
from analysis.extraction.keyphrase_extractor import extract_keyphrases
from analysis.extraction.phrase_extractor import extract_phrases


class TriggerExtractor:
    def extract_all(
        self,
        prompt_runs: list[dict[str, Any]],
        fragments_by_run: dict[str, list[dict[str, Any]]],
        facts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        phrase_map = extract_phrases(prompt_runs, fragments_by_run)
        keyphrase_map = extract_keyphrases(prompt_runs, fragments_by_run)
        entity_map = extract_entities(prompt_runs, fragments_by_run, facts)
        merged = merge_provenance_maps(phrase_map, keyphrase_map, entity_map)
        return merged

    def to_candidates(
        self,
        provenance_map: dict[str, Any],
        *,
        brand_id: str,
        batch_run_id: str,
        prompt_runs: list[dict[str, Any]],
        intent_by_prompt: dict[str, str],
    ) -> list[dict[str, Any]]:
        return to_candidates(
            provenance_map,
            brand_id=brand_id,
            batch_run_id=batch_run_id,
            total_runs=len(prompt_runs),
            intent_by_prompt=intent_by_prompt,
            prompt_runs=prompt_runs,
        )
