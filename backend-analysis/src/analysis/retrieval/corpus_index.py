"""Build searchable document text from normalized facts."""

from __future__ import annotations

import re
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]{1,}")

LIST_FIELDS = (
    "features",
    "pain_points",
    "brand_phrases",
    "products",
    "pricing_terms",
    "industries",
    "competitor_mentions",
    "customer_types",
)


def tokenise(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def fact_to_document(fact: dict[str, Any]) -> str:
    parts = [fact.get("title") or "", fact.get("summary") or ""]
    for field in LIST_FIELDS:
        parts.append(" ".join(fact.get(field) or []))
    return " ".join(p for p in parts if p)


def build_corpus(facts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    documents = [tokenise(fact_to_document(f)) for f in facts]
    return facts, documents
