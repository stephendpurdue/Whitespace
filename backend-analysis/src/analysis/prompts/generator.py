"""Synthetic prompt generation from brand facts."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from analysis.prompts.llm_client import generate_llm_prompts, llm_enabled
from analysis.prompts.templates import (
    HIGH_INTENT,
    INTENT_BUCKETS,
    PERSONAS,
    build_fact_slots,
    render_template,
)


class PromptGenerator:
    def generate(self, brand_id: str, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        slots = build_fact_slots(facts)
        prompts: list[dict[str, Any]] = []
        slot_index = 0

        for intent in INTENT_BUCKETS:
            for persona in PERSONAS:
                llm_prompts = None
                if llm_enabled():
                    llm_prompts = generate_llm_prompts(
                        brand_id, facts, intent=intent, persona=persona, count=1
                    )
                if llm_prompts:
                    prompts.extend(llm_prompts)
                    continue

                slot = slots[slot_index % len(slots)]
                slot_index += 1
                text = render_template(intent, persona, slot)
                if not text:
                    continue
                seed_id = slot.get("normalized_fact_id")
                prompts.append(
                    {
                        "prompt_id": str(uuid4()),
                        "brand_id": brand_id,
                        "text": text,
                        "intent_bucket": intent,
                        "persona": persona,
                        "is_high_intent": intent in HIGH_INTENT,
                        "seed_fact_ids": [seed_id] if seed_id else [],
                    }
                )
        return prompts
