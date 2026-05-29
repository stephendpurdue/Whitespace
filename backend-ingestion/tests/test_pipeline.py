from ingestion.pipeline import batch_status, merge_pages


def test_merge_pages_prefers_longer_content():
    pages = merge_pages(
        [
            {"url": "https://a.com", "raw_content": "short"},
            {"url": "https://a.com", "raw_content": "much longer content"},
        ]
    )
    assert len(pages) == 1
    assert pages[0]["raw_content"] == "much longer content"


def test_merge_pages_skips_empty_url():
    assert merge_pages([{"url": "", "raw_content": "x"}]) == []


def test_batch_status_completed():
    assert batch_status([], [{"id": 1}], [{"url": "https://a.com"}]) == "completed"


def test_batch_status_failed():
    assert batch_status([{"code": "ERR"}], [], []) == "failed"


def test_batch_status_partial_on_errors_with_facts():
    assert batch_status([{"code": "ERR"}], [{"id": 1}], []) == "partial"
