"""Per-phrase provenance across prompt runs and fragments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PhraseProvenance:
    phrase: str
    phrase_type: str
    appearance_count: int = 0
    prompt_run_ids: list[str] = field(default_factory=list)
    source_page_ids: list[str] = field(default_factory=list)
    rank_positions: list[float] = field(default_factory=list)

    def record(
        self,
        *,
        prompt_run_id: str,
        source_page_ids: list[str],
        rank_positions: list[float],
    ) -> None:
        self.appearance_count += 1
        if prompt_run_id not in self.prompt_run_ids:
            self.prompt_run_ids.append(prompt_run_id)
        for sid in source_page_ids:
            if sid and sid not in self.source_page_ids:
                self.source_page_ids.append(sid)
        self.rank_positions.extend(rank_positions)


def normalise_phrase(phrase: str) -> str:
    return " ".join(phrase.lower().split())
