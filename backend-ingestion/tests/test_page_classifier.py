from ingestion.page_classifier import classify_page


def test_homepage():
    assert classify_page("https://acme.com/") == "homepage"
    assert classify_page("https://acme.com") == "homepage"


def test_pricing_and_product_paths():
    assert classify_page("https://acme.com/pricing") == "pricing"
    assert classify_page("https://acme.com/products/analytics") == "product"


def test_blog_and_comparison():
    assert classify_page("https://acme.com/blog/post-1") == "blog"
    assert classify_page("https://acme.com/compare/rival") == "comparison"
