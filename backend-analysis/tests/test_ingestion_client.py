import json

import httpx
import pytest

from analysis.ingestion_client import IngestionClient, IngestionNotReadyError


def test_load_facts_from_local_file(test_settings, tmp_path):
    brand_id = "brand-local-1"
    facts_path = (
        tmp_path
        / "brands"
        / brand_id
        / "ingestion"
        / "normalized"
        / "facts.jsonl"
    )
    facts_path.parent.mkdir(parents=True)
    row = {
        "normalized_fact_id": "f1",
        "brand_id": brand_id,
        "source_page_id": "s1",
        "url": "https://a.com",
        "page_type": "homepage",
        "last_crawled_at": "2026-05-28T12:00:00Z",
    }
    facts_path.write_text(json.dumps(row) + "\n")

    client = IngestionClient(test_settings)
    assert len(client.load_facts(brand_id)) == 1


def test_load_facts_raises_when_missing(test_settings):
    client = IngestionClient(test_settings)
    with pytest.raises(IngestionNotReadyError):
        client.load_facts("missing-brand")


def test_load_facts_falls_back_to_api(test_settings, monkeypatch):
    brand_id = "brand-api-1"

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            assert url.endswith(f"/brands/{brand_id}/facts")
            request = httpx.Request("GET", url)
            return httpx.Response(
                200,
                json=[{"normalized_fact_id": "f1", "brand_id": brand_id}],
                request=request,
            )

    monkeypatch.setattr(httpx, "Client", FakeClient)
    client = IngestionClient(test_settings)
    assert len(client.load_facts(brand_id)) == 1


def test_list_brands_with_facts(test_settings, tmp_path):
    brand_id = "brand-list-1"
    brand_dir = tmp_path / "brands" / brand_id
    brand_dir.mkdir(parents=True)
    (brand_dir / "brand.json").write_text(
        json.dumps({"brand_id": brand_id, "name": "Acme", "primary_domain": "acme.com"})
    )
    facts = brand_dir / "ingestion" / "normalized" / "facts.jsonl"
    facts.parent.mkdir(parents=True)
    facts.write_text("{}\n")

    listed = IngestionClient(test_settings).list_brands_with_facts()
    assert listed[0]["brand_id"] == brand_id
    assert listed[0]["fact_count"] == 1
