from ingestion.models import Brand, BrandInput
from ingestion.storage.repository import BrandRepository, _url_path_slug


def test_url_path_slug():
    assert _url_path_slug("https://acme.com/pricing/plans") == "pricing_plans"


def test_save_brand_and_jsonl(mock_settings):
    repo = BrandRepository(mock_settings)
    brand = Brand.from_input(BrandInput(name="A", primary_domain="a.com"))
    repo.save_brand(brand.to_dict())

    rows = [{"id": "1"}, {"id": "2"}]
    path = repo.ingestion_dir(brand.brand_id) / "normalized" / "facts.jsonl"
    repo.write_jsonl(path, rows)
    assert repo.read_jsonl(path) == rows
    assert len(repo.list_brands()) == 1


def test_save_raw_content(mock_settings):
    repo = BrandRepository(mock_settings)
    raw_dir = mock_settings.data_dir / "raw"
    rel = repo.save_raw_content(raw_dir, "https://acme.com/pricing", "# Pricing")
    assert rel.startswith("raw/")
    assert (raw_dir / rel.split("/", 1)[1]).read_text() == "# Pricing"


def test_read_batch_run_missing(mock_settings):
    repo = BrandRepository(mock_settings)
    assert repo.read_batch_run("missing-id") is None
