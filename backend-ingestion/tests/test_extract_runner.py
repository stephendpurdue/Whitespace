from ingestion.extract_runner import ExtractRunner, _url_priority


class _FakeClient:
    def __init__(self) -> None:
        self.last_urls: list[str] = []

    def extract(self, urls: list[str]) -> list[dict]:
        self.last_urls = urls
        return [{"url": u, "raw_content": "body", "source_type": "tavily_extract"} for u in urls]


def test_url_priority_ordering():
    assert _url_priority("https://acme.com/") < _url_priority("https://acme.com/pricing")
    assert _url_priority("https://acme.com/pricing") < _url_priority("https://acme.com/blog/x")
    assert _url_priority("https://acme.com/unknown-page") == 99


def test_prioritize_urls_puts_pricing_first():
    runner = ExtractRunner(_FakeClient())  # type: ignore[arg-type]
    urls = [
        "https://acme.com/blog/post",
        "https://acme.com/pricing",
        "https://acme.com/",
    ]
    ordered = runner.prioritize_urls(urls)
    assert ordered[0] in ("https://acme.com/", "https://acme.com")
    assert "pricing" in ordered[1]


def test_run_calls_extract_with_prioritized_urls():
    client = _FakeClient()
    runner = ExtractRunner(client)  # type: ignore[arg-type]
    result = runner.run(["https://acme.com/z", "https://acme.com/pricing"])
    assert len(result) == 2
    assert client.last_urls[0] == "https://acme.com/pricing"
