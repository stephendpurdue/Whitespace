"""Run prompts against in-memory corpus built from normalized facts."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from analysis.models import utc_now
from analysis.retrieval.bm25_index import Bm25Index
from analysis.retrieval.corpus_index import fact_to_document


class RetrievalRunner:
    def __init__(self, facts: list[dict[str, Any]]) -> None:
        self._facts = facts
        self._mode = os.getenv("RETRIEVAL_MODE", "bm25").lower()
        self._bm25 = Bm25Index(facts)
        self._embedding_index = None
        if self._mode == "embeddings":
            try:
                from analysis.retrieval.embedding_index import EmbeddingIndex

                model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                self._embedding_index = EmbeddingIndex(facts, model_name=model)
            except ImportError:
                self._mode = "bm25"

    def run_prompt(self, prompt: dict[str, Any]) -> dict[str, Any]:
        query = prompt["text"]
        top = self._search(query)

        fragments = []
        source_page_ids = []
        max_score = top[0][0] if top else 1.0

        for rank, (score, fact) in enumerate(top, start=1):
            sid = fact.get("source_page_id", "")
            if sid:
                source_page_ids.append(sid)
            snippet = fact.get("summary") or fact.get("title", "")
            fragments.append(
                {
                    "response_fragment_id": str(uuid4()),
                    "text": snippet,
                    "source_page_id": sid,
                    "rank_position": rank,
                    "snippet_score": round(score / max_score, 4) if max_score else 0.0,
                }
            )

        return {
            "prompt_run_id": str(uuid4()),
            "prompt_id": prompt["prompt_id"],
            "brand_id": prompt["brand_id"],
            "status": "completed",
            "source_page_ids": list(dict.fromkeys(source_page_ids)),
            "response_text": "\n".join(f["text"] for f in fragments),
            "fragments": fragments,
            "ran_at": utc_now(),
        }

    def _search(self, query: str, top_k: int = 5) -> list[tuple[float, dict[str, Any]]]:
        if self._mode == "embeddings" and self._embedding_index:
            return self._embedding_index.search(query, top_k=top_k)
        results = self._bm25.search(query, top_k=top_k)
        if results:
            return results
        return _fallback_overlap(query, self._facts, top_k)


def _fallback_overlap(
    query: str, facts: list[dict[str, Any]], top_k: int
) -> list[tuple[float, dict[str, Any]]]:
    query_terms = set(query.lower().split())
    scored: list[tuple[float, dict[str, Any]]] = []
    for fact in facts:
        blob = fact_to_document(fact).lower()
        overlap = len(query_terms & set(blob.split()))
        if overlap:
            scored.append((float(overlap), fact))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]
