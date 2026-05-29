"""BM25 retrieval over the fact corpus."""

from __future__ import annotations

from typing import Any

from rank_bm25 import BM25Okapi

from analysis.retrieval.corpus_index import build_corpus, tokenise


class Bm25Index:
    def __init__(self, facts: list[dict[str, Any]]) -> None:
        self._facts, self._documents = build_corpus(facts)
        self._bm25 = BM25Okapi(self._documents) if self._documents else None

    def search(self, query: str, *, top_k: int = 5) -> list[tuple[float, dict[str, Any]]]:
        if not self._bm25 or not self._facts:
            return []
        tokens = tokenise(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(
            ((float(s), f) for s, f in zip(scores, self._facts)),
            key=lambda x: x[0],
            reverse=True,
        )
        return [(s, f) for s, f in ranked if s > 0][:top_k]
