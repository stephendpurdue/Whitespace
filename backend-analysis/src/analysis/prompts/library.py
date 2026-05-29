"""Load/save prompt library JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PromptLibrary:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, prompts: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            for p in prompts:
                f.write(json.dumps(p) + "\n")

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]
