"""Convert extracted pages into NormalizedFact schema."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ingestion.models import utc_now
from ingestion.normalization.facts import extract_facts, strip_boilerplate
from ingestion.page_classifier import classify_page
from ingestion.tavily_client import content_hash


class NormalizationPipeline:
    def run(
        self,
        brand_id: str,
        raw_pages: list[dict[str, Any]],
        *,
        brand_name: str = "",
        competitor_domains: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Returns (source_pages, normalized_facts).
        Deduplicate by content_hash; strip boilerplate; tag confidence.
        """
        source_pages: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        seen_hashes: set[str] = set()

        for page in raw_pages:
            url = page.get("url", "")
            raw_content = page.get("raw_content", "") or page.get("content", "")
            cleaned = strip_boilerplate(raw_content)
            page_hash = page.get("content_hash") or content_hash(cleaned or url)

            if page_hash in seen_hashes:
                continue
            seen_hashes.add(page_hash)

            page_type = page.get("page_type") or classify_page(
                url,
                title=page.get("title", ""),
                content=cleaned,
            )
            extracted = extract_facts(
                cleaned,
                brand_name=brand_name,
                competitor_domains=competitor_domains,
            )
            title = page.get("title") or extracted["title"]
            confidence = page.get("confidence", extracted["confidence"])
            source_type = page.get("source_type", "tavily_extract")
            crawled_at = page.get("last_crawled_at") or utc_now()

            source_page_id = str(uuid4())
            raw_path = page.get("raw_content_path")

            source_pages.append(
                {
                    "source_page_id": source_page_id,
                    "brand_id": brand_id,
                    "url": url,
                    "page_type": page_type,
                    "title": title,
                    "raw_content_path": raw_path,
                    "confidence": confidence,
                    "source_type": source_type,
                    "last_crawled_at": crawled_at,
                    "content_hash": page_hash,
                }
            )
            facts.append(
                {
                    "normalized_fact_id": str(uuid4()),
                    "brand_id": brand_id,
                    "source_page_id": source_page_id,
                    "url": url,
                    "page_type": page_type,
                    "title": title,
                    "summary": extracted["summary"],
                    "products": extracted["products"],
                    "features": extracted["features"],
                    "pain_points": extracted["pain_points"],
                    "customer_types": extracted["customer_types"],
                    "industries": extracted["industries"],
                    "pricing_terms": extracted["pricing_terms"],
                    "brand_phrases": extracted["brand_phrases"],
                    "competitor_mentions": extracted["competitor_mentions"],
                    "confidence": confidence,
                    "source_type": source_type,
                    "last_crawled_at": crawled_at,
                }
            )

        return source_pages, facts
