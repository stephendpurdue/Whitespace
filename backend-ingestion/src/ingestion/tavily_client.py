"""Thin wrapper around Tavily Crawl and Extract APIs."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from ingestion.settings import Settings

TAVILY_BASE = "https://api.tavily.com"
EXTRACT_BATCH_SIZE = 20


class TavilyAPIError(Exception):
    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class TavilyClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._mock = settings.tavily_mock
        self._client = httpx.Client(
            base_url=TAVILY_BASE,
            headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
            timeout=120.0,
        )

    def crawl(
        self,
        domain: str,
        *,
        max_depth: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """Discover and extract pages on a domain via POST /crawl."""
        if self._mock:
            return self._mock_crawl(domain)

        url = _root_url(domain)
        payload: dict[str, Any] = {
            "url": url,
            "max_depth": max_depth if max_depth is not None else self._settings.crawl_max_depth,
            "limit": limit if limit is not None else self._settings.crawl_limit,
            "extract_depth": self._settings.extract_depth,
            "format": "markdown",
            "allow_external": False,
        }
        data = self._post("/crawl", payload)
        pages = [
            {
                "url": item.get("url", ""),
                "raw_content": item.get("raw_content", ""),
                "source_type": "tavily_crawl",
            }
            for item in data.get("results", [])
            if item.get("url")
        ]
        return {"base_url": data.get("base_url", url), "pages": pages}

    def extract(self, urls: list[str]) -> list[dict[str, Any]]:
        """Extract content from URLs via POST /extract (batched, max 20 per call)."""
        if not urls:
            return []
        if self._mock:
            return self._mock_extract(urls)

        pages: list[dict[str, Any]] = []
        for batch_start in range(0, len(urls), EXTRACT_BATCH_SIZE):
            batch = urls[batch_start : batch_start + EXTRACT_BATCH_SIZE]
            payload = {
                "urls": batch,
                "extract_depth": self._settings.extract_depth,
                "format": "markdown",
            }
            data = self._post("/extract", payload)
            for item in data.get("results", []):
                if item.get("url"):
                    pages.append(
                        {
                            "url": item["url"],
                            "raw_content": item.get("raw_content", ""),
                            "source_type": "tavily_extract",
                        }
                    )
        return pages

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._settings.tavily_api_key:
            raise TavilyAPIError("TAVILY_API_KEY is not set")
        try:
            response = self._client.post(path, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _error_detail(exc.response)
            raise TavilyAPIError(
                detail or f"Tavily {path} failed: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise TavilyAPIError(f"Tavily {path} request failed: {exc}") from exc
        return response.json()

    def _mock_crawl(self, domain: str) -> dict[str, Any]:
        root = _root_url(domain)
        host = urlparse(root).netloc
        return {
            "base_url": root,
            "pages": [
                {
                    "url": root,
                    "raw_content": (
                        f"# {host}\n\n"
                        "Welcome to our analytics platform. "
                        "Track funnels, retention, and product usage in one dashboard."
                    ),
                    "source_type": "tavily_crawl",
                },
                {
                    "url": f"{root.rstrip('/')}/pricing",
                    "raw_content": (
                        "# Pricing\n\n"
                        "Starter: $49 per month for small teams.\n"
                        "Growth: $199 per month with advanced reporting.\n"
                        "Enterprise: custom pricing."
                    ),
                    "source_type": "tavily_crawl",
                },
                {
                    "url": f"{root.rstrip('/')}/product",
                    "raw_content": (
                        "# Product\n\n"
                        "Features: real-time dashboards, funnel analysis, cohort reports.\n"
                        "Built for product managers and growth teams."
                    ),
                    "source_type": "tavily_crawl",
                },
            ],
        }

    def _mock_extract(self, urls: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "url": url,
                "raw_content": f"# Extracted\n\nMock content for {url}",
                "source_type": "tavily_extract",
            }
            for url in urls
        ]

    def close(self) -> None:
        self._client.close()


def _root_url(domain: str) -> str:
    domain = domain.strip()
    if domain.startswith("http://") or domain.startswith("https://"):
        return domain.rstrip("/")
    return f"https://{domain.lstrip('.')}"


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text or ""
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, dict) and detail.get("error"):
            return str(detail["error"])
        if isinstance(detail, str):
            return detail
        if body.get("error"):
            return str(body["error"])
    return ""


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
