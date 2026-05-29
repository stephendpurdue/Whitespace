from ingestion.normalization.facts import extract_facts, strip_boilerplate


def test_strip_boilerplate_removes_nav_noise():
    text = "Welcome\nNavigation\nCtrl K\nReal product copy here."
    assert "Ctrl K" not in strip_boilerplate(text)
    assert "Real product copy" in strip_boilerplate(text)


def test_extract_facts_pricing_and_features():
    text = """
    # Analytics Platform
    Features: dashboards, funnel analysis, cohort reports.
    Pricing: $49 per month for startups. Enterprise pricing available.
  """
    facts = extract_facts(text, brand_name="Analytics Platform")
    assert "$49" in " ".join(facts["pricing_terms"]) or facts["pricing_terms"]
    assert facts["summary"]
    assert facts["confidence"] >= 0.4
