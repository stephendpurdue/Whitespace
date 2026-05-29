"""Merge phrase provenance into trigger candidates."""

from __future__ import annotations

from typing import Any

from analysis.extraction.intent_resolver import resolve_intent_bucket
from analysis.extraction.provenance import PhraseProvenance, normalise_phrase


def merge_provenance_maps(
    *maps: dict[str, PhraseProvenance],
) -> dict[str, PhraseProvenance]:
    merged: dict[str, PhraseProvenance] = {}
    for prov_map in maps:
        for key, prov in prov_map.items():
            norm = normalise_phrase(key)
            if norm not in merged:
                merged[norm] = PhraseProvenance(
                    phrase=norm,
                    phrase_type=prov.phrase_type,
                    appearance_count=prov.appearance_count,
                    prompt_run_ids=list(prov.prompt_run_ids),
                    source_page_ids=list(prov.source_page_ids),
                    rank_positions=list(prov.rank_positions),
                )
                continue
            target = merged[norm]
            if _type_priority(prov.phrase_type) > _type_priority(target.phrase_type):
                target.phrase_type = prov.phrase_type
            target.appearance_count += prov.appearance_count
            for run_id in prov.prompt_run_ids:
                if run_id not in target.prompt_run_ids:
                    target.prompt_run_ids.append(run_id)
            for sid in prov.source_page_ids:
                if sid and sid not in target.source_page_ids:
                    target.source_page_ids.append(sid)
            target.rank_positions.extend(prov.rank_positions)
    return merged


def to_candidates(
    provenance_map: dict[str, PhraseProvenance],
    *,
    brand_id: str,
    batch_run_id: str,
    total_runs: int,
    intent_by_prompt: dict[str, str],
    prompt_runs: list[dict[str, Any]],
    limit: int = 150,
) -> list[dict[str, Any]]:
    run_by_id = {r["prompt_run_id"]: r for r in prompt_runs}
    sorted_items = sorted(
        provenance_map.values(),
        key=lambda p: p.appearance_count,
        reverse=True,
    )[:limit]

    candidates: list[dict[str, Any]] = []
    for prov in sorted_items:
        intents = [
            intent_by_prompt.get(run_by_id[rid]["prompt_id"], "mixed")
            for rid in prov.prompt_run_ids
            if rid in run_by_id
        ]
        appearance_rate = prov.appearance_count / max(total_runs, 1)
        avg_rank = (
            sum(prov.rank_positions) / len(prov.rank_positions)
            if prov.rank_positions
            else None
        )
        candidates.append(
            {
                "phrase": prov.phrase,
                "phrase_type": prov.phrase_type,
                "appearance_count": prov.appearance_count,
                "appearance_rate": min(1.0, appearance_rate),
                "intent_bucket": resolve_intent_bucket(intents),
                "brand_id": brand_id,
                "batch_run_id": batch_run_id,
                "prompt_run_ids": prov.prompt_run_ids[:20],
                "source_page_ids": prov.source_page_ids[:20],
                "avg_rank_position": avg_rank,
            }
        )
    return candidates


def _type_priority(phrase_type: str) -> int:
    order = {"entity": 4, "keyphrase": 3, "bigram": 2, "unigram": 1}
    return order.get(phrase_type, 0)
