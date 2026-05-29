"""Domain models aligned with shared/schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BrandInput:
    name: str
    primary_domain: str
    competitor_domains: list[str] = field(default_factory=list)
    seed_topics: list[str] = field(default_factory=list)


@dataclass
class Brand:
    brand_id: str
    name: str
    primary_domain: str
    competitor_domains: list[str]
    seed_topics: list[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_input(cls, inp: BrandInput) -> Brand:
        now = utc_now()
        return cls(
            brand_id=str(uuid4()),
            name=inp.name,
            primary_domain=inp.primary_domain,
            competitor_domains=inp.competitor_domains,
            seed_topics=inp.seed_topics,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "name": self.name,
            "primary_domain": self.primary_domain,
            "competitor_domains": self.competitor_domains,
            "seed_topics": self.seed_topics,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
