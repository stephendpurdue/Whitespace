"""Orchestrates Tavily extract for prioritized URLs."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from ingestion.tavily_client import TavilyClient

PRIORITY_PATH_HINTS = (
    "/pricing",
    "/product",
    "/docs",
    "/blog",
    "/compare",
)


class ExtractRunner:
    def __init__(self, client: TavilyClient) -> None:
        self._client = client

    def prioritize_urls(self, urls: list[str], *, limit: int = 50) -> list[str]:
        """Rank URLs for extract budget (homepage, product, pricing first)."""
        return sorted(urls, key=_url_priority)[:limit]

    def run(self, urls: list[str]) -> list[dict[str, Any]]:
        return self._client.extract(self.prioritize_urls(urls))


def _url_priority(url: str) -> int:
    lower = url.lower()
    path = urlparse(lower).path.rstrip("/") or "/"
    if path == "/":
        return 0
    for index, hint in enumerate(PRIORITY_PATH_HINTS, start=1):
        if hint in lower:
            return index
    return 99
