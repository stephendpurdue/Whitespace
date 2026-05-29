"""Optional embedding retrieval (requires sentence-transformers)."""

from __future__ import annotations

from typing import Any

from analysis.retrieval.corpus_index import fact_to_document


class EmbeddingIndex:
    def __init__(self, facts: list[dict[str, Any]], model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        self._facts = facts
        self._np = np
        self._model = SentenceTransformer(model_name)
        texts = [fact_to_document(f) for f in facts]
        self._embeddings = self._model.encode(texts, normalize_embeddings=True)

    def search(self, query: str, *, top_k: int = 5) -> list[tuple[float, dict[str, Any]]]:
        if not self._facts:
            return []
        query_vec = self._model.encode([query], normalize_embeddings=True)[0]
        scores = self._embeddings @ query_vec
        ranked = sorted(
            ((float(s), f) for s, f in zip(scores, self._facts)),
            key=lambda x: x[0],
            reverse=True,
        )
        return [(s, f) for s, f in ranked if s > 0][:top_k]
