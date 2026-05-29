"""Read/write brand data under data/brands/{brand_id}."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

from ingestion.settings import Settings


class BrandRepository:
    def __init__(self, settings: Settings) -> None:
        self._root = settings.data_dir / "brands"

    def brand_dir(self, brand_id: str) -> Path:
        return self._root / brand_id

    def ingestion_dir(self, brand_id: str) -> Path:
        return self.brand_dir(brand_id) / "ingestion"

    def list_brands(self) -> list[dict[str, Any]]:
        if not self._root.exists():
            return []
        brands: list[dict[str, Any]] = []
        for d in self._root.iterdir():
            brand_file = d / "brand.json"
            if d.is_dir() and brand_file.is_file():
                brands.append(json.loads(brand_file.read_text()))
        return brands

    def save_brand(self, brand: dict[str, Any]) -> Path:
        d = self.brand_dir(brand["brand_id"])
        d.mkdir(parents=True, exist_ok=True)
        path = d / "brand.json"
        path.write_text(json.dumps(brand, indent=2))
        return path

    def write_batch_run(self, ingestion_dir: Path, batch_run: dict[str, Any]) -> Path:
        path = ingestion_dir / "batch_run.json"
        path.write_text(json.dumps(batch_run, indent=2))
        return path

    def read_batch_run(self, brand_id: str) -> Optional[dict[str, Any]]:
        path = self.ingestion_dir(brand_id) / "batch_run.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def save_raw_content(self, raw_dir: Path, url: str, content: str) -> str:
        """Persist raw markdown; return relative path under ingestion/."""
        raw_dir.mkdir(parents=True, exist_ok=True)
        slug = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", _url_path_slug(url))[:40]
        filename = f"{safe}_{slug}.md"
        path = raw_dir / filename
        path.write_text(content)
        return f"raw/{filename}"

    def write_jsonl(self, path: Path, rows: Iterable[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _url_path_slug(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_") or "index"
    return path
