"""Rules-based extraction of normalized_fact fields from page text."""

from __future__ import annotations

import re
from typing import Any

_PRICING_RE = re.compile(
    r"(?i)(\$[\d,]+(?:\.\d{2})?(?:\s*/\s*(?:mo|month|yr|year))?|"
    r"free (?:tier|plan|trial)|per (?:user|seat|month)|enterprise pricing)"
)
_FEATURE_LINE_RE = re.compile(
    r"(?i)^[\s\-\*•]+(.{8,80})$", re.MULTILINE
)
_PAIN_RE = re.compile(
    r"(?i)\b(struggle|challenge|pain|problem|friction|bottleneck|difficult)\w*\b[^.\n]{0,80}"
)
_INDUSTRY_TERMS = (
    "saas",
    "ecommerce",
    "fintech",
    "healthcare",
    "b2b",
    "b2c",
    "startup",
    "enterprise",
)
_CUSTOMER_TERMS = (
    "product manager",
    "growth team",
    "marketing team",
    "developer",
    "data team",
    "founder",
    "analyst",
)


def strip_boilerplate(text: str) -> str:
    """Remove common nav/footer noise from markdown-ish crawl output."""
    if not text:
        return ""
    lines: list[str] = []
    skip_patterns = (
        "cookie",
        "sign in",
        "log in",
        "navigation",
        "ctrl k",
        "search or ask",
    )
    for line in text.splitlines():
        lower = line.lower().strip()
        if not lower:
            continue
        if any(pat in lower for pat in skip_patterns):
            continue
        if lower.startswith("!["):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def extract_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line and len(line) < 120:
            return line
    return ""


def extract_summary(text: str, *, max_len: int = 400) -> str:
    cleaned = strip_boilerplate(text)
    if not cleaned:
        return ""
    paragraph = re.sub(r"\s+", " ", cleaned.replace("\n", " "))
    if len(paragraph) <= max_len:
        return paragraph
    cut = paragraph[:max_len]
    last_period = cut.rfind(". ")
    if last_period > 80:
        return cut[: last_period + 1]
    return cut.rstrip() + "…"


def extract_facts(
    text: str,
    *,
    brand_name: str = "",
    competitor_domains: list[str] | None = None,
) -> dict[str, Any]:
    cleaned = strip_boilerplate(text)
    lower = cleaned.lower()

    products: list[str] = []
    features: list[str] = []
    for line in cleaned.splitlines():
        line_stripped = line.strip().lstrip("#").strip()
        if re.match(r"(?i)^products?\b", line_stripped):
            continue
        if re.match(r"(?i)^(features?|capabilities)\b", line_stripped):
            continue
        match = _FEATURE_LINE_RE.match(line)
        if match:
            phrase = match.group(1).strip()
            if "feature" in lower and len(features) < 12:
                features.append(phrase)
            elif len(products) < 8:
                products.append(phrase)

    if not features:
        for m in re.finditer(r"(?i)features?:\s*([^\n]+)", cleaned):
            parts = re.split(r"[,;•\|]", m.group(1))
            features.extend(p.strip() for p in parts if 4 < len(p.strip()) < 80)

    pricing_terms = list(dict.fromkeys(_PRICING_RE.findall(cleaned)))[:12]
    pain_points = list(dict.fromkeys(m.group(0).strip() for m in _PAIN_RE.finditer(cleaned)))[:8]

    industries = [t for t in _INDUSTRY_TERMS if t in lower]
    customer_types = [t for t in _CUSTOMER_TERMS if t in lower]

    brand_phrases: list[str] = []
    if brand_name and brand_name.lower() in lower:
        brand_phrases.append(brand_name)
    for m in re.finditer(r'"([^"]{4,60})"', cleaned):
        brand_phrases.append(m.group(1))
    brand_phrases = list(dict.fromkeys(brand_phrases))[:10]

    competitor_mentions: list[str] = []
    for domain in competitor_domains or []:
        label = domain.split(".")[0]
        if domain.lower() in lower or label.lower() in lower:
            competitor_mentions.append(domain)

    confidence = 0.85 if len(cleaned) > 500 else 0.65 if len(cleaned) > 100 else 0.4

    return {
        "title": extract_title(cleaned),
        "summary": extract_summary(cleaned),
        "products": products[:8],
        "features": features[:12],
        "pain_points": pain_points,
        "customer_types": customer_types,
        "industries": industries,
        "pricing_terms": pricing_terms,
        "brand_phrases": brand_phrases,
        "competitor_mentions": competitor_mentions,
        "confidence": confidence,
    }
