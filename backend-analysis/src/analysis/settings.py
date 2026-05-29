"""Runtime configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


def _load_env() -> None:
    from dotenv import load_dotenv

    env_file = BACKEND_ROOT / ".env"
    if env_file.is_file():
        load_dotenv(env_file, override=False)
    load_dotenv(override=False)


def _resolve_path(raw: Optional[str], default: Path) -> Path:
    if not raw:
        return default
    path = Path(raw)
    if path.is_absolute():
        return path
    return (BACKEND_ROOT / path).resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    ingestion_api_url: str
    schemas_dir: Path
    scoring_config_path: Path

    @property
    def scoring_config(self) -> dict:
        return json.loads(self.scoring_config_path.read_text())


@lru_cache
def get_settings() -> Settings:
    _load_env()
    return Settings(
        data_dir=_resolve_path(os.getenv("DATA_DIR"), REPO_ROOT / "data"),
        ingestion_api_url=os.getenv("INGESTION_API_URL", "http://127.0.0.1:8001").rstrip(
            "/"
        ),
        schemas_dir=_resolve_path(
            os.getenv("SHARED_SCHEMAS_DIR"),
            REPO_ROOT / "shared" / "schemas",
        ),
        scoring_config_path=_resolve_path(
            os.getenv("SCORING_CONFIG"),
            REPO_ROOT / "shared" / "config" / "scoring.default.json",
        ),
    )


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
