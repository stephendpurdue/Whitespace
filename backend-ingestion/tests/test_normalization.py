from ingestion.normalization.pipeline import NormalizationPipeline


def test_normalization_dedupes_by_hash():
    pipeline = NormalizationPipeline()
    raw = [
        {
            "url": "https://a.com",
            "content_hash": "abc",
            "title": "A",
            "raw_content": "Same body text for dedup.",
        },
        {
            "url": "https://a.com/dup",
            "content_hash": "abc",
            "title": "A dup",
            "raw_content": "Same body text for dedup.",
        },
    ]
    pages, facts = pipeline.run("brand-1", raw)
    assert len(pages) == 1
    assert len(facts) == 1
    assert facts[0]["summary"]


def test_normalization_classifies_pricing_page():
    pipeline = NormalizationPipeline()
    raw = [
        {
            "url": "https://a.com/pricing",
            "raw_content": "# Pricing\n$99 per month\nEnterprise plan",
        }
    ]
    pages, facts = pipeline.run("brand-1", raw)
    assert pages[0]["page_type"] == "pricing"
    assert facts[0]["pricing_terms"]
