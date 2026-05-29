"""Frontend-stable ranked trigger export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_ranked_export(
    path: Path,
    *,
    brand_id: str,
    batch_run_id: str,
    scoring_config_version: str,
    triggers: list[dict[str, Any]],
) -> None:
    payload = {
        "brand_id": brand_id,
        "batch_run_id": batch_run_id,
        "scoring_config_version": scoring_config_version,
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "triggers": triggers,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
