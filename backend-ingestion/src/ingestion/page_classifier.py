"""Classify URLs into shared source_page page_type values."""

from __future__ import annotations

from urllib.parse import urlparse

PAGE_TYPES = (
    "homepage",
    "product",
    "pricing",
    "docs",
    "blog",
    "comparison",
    "other",
)

_PATH_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pricing", ("/pricing", "/plans", "/plan", "/price", "/billing")),
    ("product", ("/product", "/products", "/features", "/solutions", "/platform")),
    ("docs", ("/docs", "/documentation", "/help", "/support", "/guide", "/api")),
    ("blog", ("/blog", "/news", "/articles", "/insights", "/resources")),
    ("comparison", ("/compare", "/comparison", "/vs", "/alternatives", "/competitor")),
)


def classify_page(url: str, *, title: str = "", content: str = "") -> str:
    """Return a page_type enum value for a URL (and optional hints)."""
    parsed = urlparse(url.lower())
    path = parsed.path.rstrip("/") or "/"

    if path == "/" or path == "":
        return "homepage"

    path_lower = path.lower()
    for page_type, hints in _PATH_RULES:
        if any(hint in path_lower for hint in hints):
            return page_type

    combined = f"{title} {content}".lower()
    if any(k in combined for k in ("pricing", "per month", "free plan", "enterprise plan")):
        return "pricing"
    if any(k in combined for k in (" vs ", " compare ", " alternative to ")):
        return "comparison"

    return "other"
