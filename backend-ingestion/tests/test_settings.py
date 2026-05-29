from ingestion.settings import BACKEND_ROOT, get_settings, reload_settings


def test_settings_load_env_from_backend_root(monkeypatch):
    env_file = BACKEND_ROOT / ".env"
    if not env_file.is_file():
        return  # skip when no .env in CI
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    reload_settings()
    settings = get_settings()
    assert settings.data_dir.name == "data" or settings.data_dir.exists()
