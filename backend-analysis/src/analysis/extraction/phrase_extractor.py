"""Unigram and bigram extraction from prompt run responses."""

from __future__ import annotations

import re
from typing import Any

from analysis.extraction.provenance import PhraseProvenance, normalise_phrase

WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-]{2,}")
STOPWORDS = frozenset(
    "the a an and or for to of in on with is are was were be been being".split()
)


def extract_phrases(
    prompt_runs: list[dict[str, Any]],
    fragments_by_run: dict[str, list[dict[str, Any]]],
) -> dict[str, PhraseProvenance]:
    provenance: dict[str, PhraseProvenance] = {}

    for run in prompt_runs:
        run_id = run["prompt_run_id"]
        frags = fragments_by_run.get(run_id, [])
        source_ids = [f.get("source_page_id", "") for f in frags if f.get("source_page_id")]
        ranks = [float(f.get("rank_position", 0)) for f in frags if f.get("rank_position")]

        text = (run.get("response_text") or "").lower()
        tokens = [t for t in WORD_RE.findall(text) if t not in STOPWORDS]

        for token in tokens:
            _record(provenance, token, "unigram", run_id, source_ids, ranks)
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            _record(provenance, bigram, "bigram", run_id, source_ids, ranks)

    return provenance


def _record(
    provenance: dict[str, PhraseProvenance],
    phrase: str,
    phrase_type: str,
    run_id: str,
    source_ids: list[str],
    ranks: list[float],
) -> None:
    key = normalise_phrase(phrase)
    if key not in provenance:
        provenance[key] = PhraseProvenance(phrase=key, phrase_type=phrase_type)
    provenance[key].record(
        prompt_run_id=run_id,
        source_page_ids=source_ids,
        rank_positions=ranks,
    )
