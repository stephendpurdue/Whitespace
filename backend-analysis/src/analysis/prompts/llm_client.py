"""Optional LLM prompt variety via OpenAI-compatible API."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from analysis.prompts.templates import INTENT_BUCKETS


def llm_enabled() -> bool:
    return os.getenv("PROMPT_LLM_ENABLED", "false").lower() in ("1", "true", "yes")


def generate_llm_prompts(
    brand_id: str,
    facts: list[dict[str, Any]],
    *,
    intent: str,
    persona: str,
    count: int = 2,
) -> list[dict[str, Any]] | None:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("PROMPT_LLM_MODEL", "gpt-4o-mini")
    summary = _compact_facts(facts)

    system = (
        "Generate realistic user search prompts as JSON. "
        'Return {"prompts": ["...", "..."]} only.'
    )
    user = (
        f"Brand facts: {summary}\n"
        f"Intent: {intent}\nPersona: {persona}\n"
        f"Generate {count} distinct prompts."
    )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            texts = parsed.get("prompts", [])
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError):
        return None

    if intent not in INTENT_BUCKETS:
        return None

    from uuid import uuid4

    seed_ids = [
        f.get("normalized_fact_id")
        for f in facts[:3]
        if f.get("normalized_fact_id")
    ]
    return [
        {
            "prompt_id": str(uuid4()),
            "brand_id": brand_id,
            "text": text,
            "intent_bucket": intent,
            "persona": persona,
            "is_high_intent": intent in ("transactional", "comparison", "alternative_switching"),
            "seed_fact_ids": seed_ids,
        }
        for text in texts
        if isinstance(text, str) and text.strip()
    ]


def _compact_facts(facts: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for fact in facts[:5]:
        lines.append(
            f"- {fact.get('title', '')}: {fact.get('summary', '')[:200]}"
        )
    return "\n".join(lines)
