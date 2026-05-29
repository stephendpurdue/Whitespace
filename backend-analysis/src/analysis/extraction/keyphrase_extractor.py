"""RAKE-style keyphrase extraction from prompt run responses."""

from __future__ import annotations

import re
from typing import Any

from analysis.extraction.provenance import PhraseProvenance, normalise_phrase

WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-]{2,}")
STOPWORDS = frozenset(
    "the a an and or for to of in on with is are was were be been being that this".split()
)
MIN_PHRASE_WORDS = 2
MAX_PHRASE_WORDS = 4


def extract_keyphrases(
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
        phrases = _rake_phrases(tokens)

        for phrase in phrases:
            key = normalise_phrase(phrase)
            if key not in provenance:
                provenance[key] = PhraseProvenance(phrase=key, phrase_type="keyphrase")
            provenance[key].record(
                prompt_run_id=run_id,
                source_page_ids=source_ids,
                rank_positions=ranks,
            )

    return provenance


def _rake_phrases(tokens: list[str]) -> list[str]:
    if len(tokens) < MIN_PHRASE_WORDS:
        return []
    phrases: list[str] = []
    buffer: list[str] = []
    for token in tokens:
        if token in STOPWORDS:
            if len(buffer) >= MIN_PHRASE_WORDS:
                phrases.append(" ".join(buffer[:MAX_PHRASE_WORDS]))
            buffer = []
        else:
            buffer.append(token)
            if len(buffer) > MAX_PHRASE_WORDS:
                buffer = buffer[-MAX_PHRASE_WORDS:]
    if len(buffer) >= MIN_PHRASE_WORDS:
        phrases.append(" ".join(buffer[:MAX_PHRASE_WORDS]))
    return phrases
