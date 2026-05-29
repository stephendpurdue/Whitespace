from ingestion.models import BrandInput
from ingestion.pipeline import IngestionPipeline


def test_full_ingestion_mock(mock_settings):
    pipeline = IngestionPipeline(mock_settings)
    try:
        result = pipeline.run(
            BrandInput(
                name="Acme",
                primary_domain="acme.com",
                competitor_domains=["rival.com"],
            )
        )
    finally:
        pipeline.close()

    assert result["status"] == "completed"
    assert result["normalized_facts"] >= 1

    ing = mock_settings.data_dir / "brands" / result["brand_id"] / "ingestion"
    assert (ing / "normalized" / "facts.jsonl").exists()
    assert (ing / "source_pages.jsonl").exists()
    assert (ing / "batch_run.json").exists()
