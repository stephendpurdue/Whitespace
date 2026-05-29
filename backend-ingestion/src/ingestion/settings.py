"""Runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

# backend-ingestion/ (contains .env)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


def _load_env() -> None:
    """Load backend-ingestion/.env regardless of shell cwd."""
    from dotenv import load_dotenv

    env_file = BACKEND_ROOT / ".env"
    if env_file.is_file():
        load_dotenv(env_file, override=False)
    # Optional override from cwd (e.g. monorepo root .env)
    load_dotenv(override=False)


def _resolve_path(raw: Optional[str], default: Path) -> Path:
    if not raw:
        return default
    path = Path(raw)
    if path.is_absolute():
        return path
    # Paths like ../data are relative to backend-ingestion/
    return (BACKEND_ROOT / path).resolve()


@dataclass(frozen=True)
class Settings:
    tavily_api_key: str
    tavily_mock: bool
    data_dir: Path
    schemas_dir: Path
    crawl_max_depth: int
    crawl_limit: int
    extract_depth: str


@lru_cache
def get_settings() -> Settings:
    _load_env()
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    mock_env = os.getenv("TAVILY_MOCK", "").strip().lower() in ("1", "true", "yes")
    return Settings(
        tavily_api_key=api_key,
        tavily_mock=mock_env or not api_key,
        data_dir=_resolve_path(
            os.getenv("DATA_DIR"),
            REPO_ROOT / "data",
        ),
        schemas_dir=_resolve_path(
            os.getenv("SHARED_SCHEMAS_DIR"),
            REPO_ROOT / "shared" / "schemas",
        ),
        crawl_max_depth=int(os.getenv("CRAWL_MAX_DEPTH", "2")),
        crawl_limit=int(os.getenv("CRAWL_LIMIT", "30")),
        extract_depth=os.getenv("EXTRACT_DEPTH", "basic"),
    )


def reload_settings() -> Settings:
    """Clear cached settings after .env changes (tests / hot reload)."""
    get_settings.cache_clear()
    return get_settings()
