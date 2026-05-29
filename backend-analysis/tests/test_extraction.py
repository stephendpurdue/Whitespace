"""Tests for phrase, keyphrase, entity extraction and candidate merging."""

from __future__ import annotations

from analysis.extraction.candidate_merger import merge_provenance_maps, to_candidates
from analysis.extraction.entity_extractor import extract_entities, known_entities_from_facts
from analysis.extraction.keyphrase_extractor import extract_keyphrases
from analysis.extraction.phrase_extractor import extract_phrases
from analysis.extraction.provenance import PhraseProvenance, normalise_phrase
from analysis.extraction.trigger_extractor import TriggerExtractor


def _run(
    run_id: str,
    prompt_id: str,
    text: str,
    *,
    source_page_id: str = "page-1",
) -> dict:
    return {
        "prompt_run_id": run_id,
        "prompt_id": prompt_id,
        "response_text": text,
    }


def _fragments(run_id: str, source_page_id: str = "page-1") -> list[dict]:
    return [
        {
            "prompt_run_id": run_id,
            "source_page_id": source_page_id,
            "rank_position": 1,
            "text": "snippet",
        }
    ]


def test_normalise_phrase_collapses_whitespace():
    assert normalise_phrase("  Funnel   Reporting  ") == "funnel reporting"


def test_phrase_extractor_tracks_per_run_provenance():
    runs = [
        _run("run-a", "prompt-a", "funnel reporting helps teams"),
        _run("run-b", "prompt-b", "pricing per seat only"),
    ]
    fragments_by_run = {
        "run-a": _fragments("run-a", "src-a"),
        "run-b": _fragments("run-b", "src-b"),
    }
    provenance = extract_phrases(runs, fragments_by_run)

    assert "funnel" in provenance
    assert provenance["funnel"].prompt_run_ids == ["run-a"]
    assert "src-a" in provenance["funnel"].source_page_ids
    assert "pricing" in provenance
    assert provenance["pricing"].prompt_run_ids == ["run-b"]


def test_keyphrase_extractor_finds_multi_word_phrases():
    runs = [_run("run-1", "p1", "teams need funnel reporting for growth")]
    fragments_by_run = {"run-1": _fragments("run-1")}
    provenance = extract_keyphrases(runs, fragments_by_run)

    keys = set(provenance.keys())
    assert any("funnel" in k for k in keys)


def test_entity_extractor_finds_known_competitors():
    facts = [{"competitor_mentions": ["Rival Metrics"], "products": [], "brand_phrases": []}]
    runs = [_run("run-1", "p1", "Teams switch from Rival Metrics to Acme")]
    fragments_by_run = {"run-1": _fragments("run-1")}

    provenance = extract_entities(runs, fragments_by_run, facts)
    assert "rival metrics" in provenance
    assert provenance["rival metrics"].phrase_type == "entity"


def test_known_entities_from_facts():
    facts = [
        {
            "competitor_mentions": ["Rival Metrics"],
            "products": ["Acme Platform"],
            "brand_phrases": ["Acme Analytics"],
            "customer_types": [],
        }
    ]
    known = known_entities_from_facts(facts)
    assert "rival metrics" in known
    assert "acme platform" in known


def test_merge_provenance_prefers_higher_phrase_type():
    unigram = {"funnel": PhraseProvenance("funnel", "unigram", appearance_count=2)}
    entity = {"funnel": PhraseProvenance("funnel", "entity", appearance_count=1)}
    merged = merge_provenance_maps(unigram, entity)
    assert merged["funnel"].phrase_type == "entity"
    assert merged["funnel"].appearance_count == 3


def test_to_candidates_resolves_single_intent_bucket():
    prov = PhraseProvenance("funnel reporting", "bigram", appearance_count=3)
    prov.record(prompt_run_id="run-1", source_page_ids=["src-1"], rank_positions=[1.0])
    prov.record(prompt_run_id="run-2", source_page_ids=["src-1"], rank_positions=[2.0])

    runs = [
        {"prompt_run_id": "run-1", "prompt_id": "p1"},
        {"prompt_run_id": "run-2", "prompt_id": "p2"},
    ]
    intent_by_prompt = {"p1": "transactional", "p2": "transactional"}

    candidates = to_candidates(
        {"funnel reporting": prov},
        brand_id="brand-1",
        batch_run_id="batch-1",
        total_runs=2,
        intent_by_prompt=intent_by_prompt,
        prompt_runs=runs,
    )
    assert candidates[0]["intent_bucket"] == "transactional"
    assert set(candidates[0]["prompt_run_ids"]) == {"run-1", "run-2"}
    assert candidates[0]["avg_rank_position"] == 1.5


def test_trigger_extractor_produces_multiple_phrase_types(sample_facts: list[dict]):
    runs = [
        _run(
            "run-1",
            "p1",
            "Rival Metrics users need funnel reporting and cohort retention.",
        )
    ]
    fragments_by_run = {"run-1": _fragments("run-1", "20000000-0000-4000-8000-000000000001")}

    extractor = TriggerExtractor()
    merged = extractor.extract_all(runs, fragments_by_run, sample_facts)
    types = {p.phrase_type for p in merged.values()}
    assert "unigram" in types or "bigram" in types
    assert "entity" in types
