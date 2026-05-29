import httpx
import pytest

from ingestion.settings import Settings
from ingestion.tavily_client import (
    TavilyAPIError,
    TavilyClient,
    _error_detail,
    _root_url,
    content_hash,
)


def test_root_url_adds_https():
    assert _root_url("acme.com") == "https://acme.com"
    assert _root_url("https://acme.com/") == "https://acme.com"


def test_content_hash_stable():
    assert content_hash("Hello   World") == content_hash("hello world")


def test_error_detail_from_json():
    response = httpx.Response(
        401,
        json={"detail": {"error": "Unauthorized"}},
        request=httpx.Request("POST", "https://api.tavily.com/crawl"),
    )
    assert _error_detail(response) == "Unauthorized"


def test_mock_crawl_returns_pages(mock_settings: Settings):
    client = TavilyClient(mock_settings)
    try:
        result = client.crawl("acme.com")
        assert len(result["pages"]) >= 1
        assert result["pages"][0]["source_type"] == "tavily_crawl"
    finally:
        client.close()


def test_extract_batches_requests(tmp_path, monkeypatch: pytest.MonkeyPatch):
    settings = Settings(
        tavily_api_key="tvly-test",
        tavily_mock=False,
        data_dir=tmp_path,
        schemas_dir=tmp_path,
        crawl_max_depth=1,
        crawl_limit=5,
        extract_depth="basic",
    )
    calls: list[list[str]] = []

    def fake_post(self, path, *, json=None, **kwargs):
        calls.append(json["urls"])
        return httpx.Response(
            200,
            json={"results": [{"url": u, "raw_content": "x"} for u in json["urls"]]},
            request=httpx.Request("POST", str(path)),
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    client = TavilyClient(settings)
    try:
        urls = [f"https://example.com/{i}" for i in range(25)]
        pages = client.extract(urls)
        assert len(pages) == 25
        assert len(calls) == 2  # 20 + 5
    finally:
        client.close()


def test_post_raises_without_api_key(tmp_path):
    settings = Settings(
        tavily_api_key="",
        tavily_mock=False,
        data_dir=tmp_path,
        schemas_dir=tmp_path,
        crawl_max_depth=1,
        crawl_limit=5,
        extract_depth="basic",
    )
    client = TavilyClient(settings)
    try:
        with pytest.raises(TavilyAPIError, match="TAVILY_API_KEY"):
            client.crawl("acme.com")
    finally:
        client.close()
