from pathlib import Path

import pytest

from ingestion.settings import Settings, reload_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    reload_settings()
    yield
    reload_settings()


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    return Settings(
        tavily_api_key="",
        tavily_mock=True,
        data_dir=tmp_path / "data",
        schemas_dir=tmp_path / "schemas",
        crawl_max_depth=1,
        crawl_limit=10,
        extract_depth="basic",
    )


@pytest.fixture
def use_mock_settings(mock_settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("ingestion.settings.get_settings", lambda: mock_settings)
    monkeypatch.setattr("ingestion.api.app.get_settings", lambda: mock_settings)
    return mock_settings
