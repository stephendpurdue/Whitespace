from analysis.retrieval.bm25_index import Bm25Index


def test_bm25_ranks_matching_fact_first():
    facts = [
        {
            "title": "Unrelated docs",
            "summary": "Generic content about weather and travel.",
            "features": [],
            "pain_points": [],
        },
        {
            "title": "Funnel reporting",
            "summary": "Build conversion funnels and compare funnel steps by channel.",
            "features": ["funnel reporting", "conversion funnels"],
            "pain_points": ["broken conversion tracking"],
        },
        {
            "title": "Pricing page",
            "summary": "Per-seat pricing and enterprise contracts.",
            "features": ["pricing"],
            "pain_points": [],
        },
    ]
    index = Bm25Index(facts)
    results = index.search("conversion funnels for marketing", top_k=2)
    assert results
    assert "funnel" in (results[0][1].get("title") or "").lower() or "funnel" in (
        results[0][1].get("summary") or ""
    ).lower()
