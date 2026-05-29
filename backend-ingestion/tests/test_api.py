import json

from fastapi.testclient import TestClient

from ingestion.api.app import app
from ingestion.models import Brand, BrandInput
from ingestion.settings import get_settings
from ingestion.storage import BrandRepository


def test_health():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "service": "ingestion"}


def test_create_brand_without_ingestion(use_mock_settings):
    mock_settings = use_mock_settings
    client = TestClient(app)
    res = client.post(
        "/brands",
        json={"name": "Test Co", "primary_domain": "test.co", "run_ingestion": False},
    )
    assert res.status_code == 202
    body = res.json()
    assert body["ingestion"] == "skipped"
    assert (mock_settings.data_dir / "brands" / body["brand_id"] / "brand.json").exists()


def test_facts_and_pages_404():
    client = TestClient(app)
    assert client.get("/brands/does-not-exist/facts").status_code == 404
    assert client.get("/brands/does-not-exist/source-pages").status_code == 404
    assert client.get("/brands/does-not-exist/batch-run").status_code == 404


def test_read_ingestion_outputs(use_mock_settings):
    mock_settings = use_mock_settings
    brand = Brand.from_input(BrandInput(name="API", primary_domain="api.test"))
    repo = BrandRepository(mock_settings)
    repo.save_brand(brand.to_dict())
    ing = repo.ingestion_dir(brand.brand_id)
    ing.mkdir(parents=True, exist_ok=True)
    repo.write_jsonl(ing / "normalized" / "facts.jsonl", [{"normalized_fact_id": "f1"}])
    repo.write_jsonl(ing / "source_pages.jsonl", [{"source_page_id": "s1"}])
    repo.write_batch_run(ing, {"batch_run_id": "b1", "status": "completed"})

    client = TestClient(app)
    assert len(client.get(f"/brands/{brand.brand_id}/facts").json()) == 1
    assert len(client.get(f"/brands/{brand.brand_id}/source-pages").json()) == 1
    assert client.get(f"/brands/{brand.brand_id}/batch-run").json()["status"] == "completed"
