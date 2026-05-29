from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from analysis.extraction.trigger_extractor import TriggerExtractor
from analysis.export.ranked_export import write_ranked_export
from analysis.ingestion_client import IngestionClient
from analysis.prompts.generator import PromptGenerator
from analysis.prompts.library import PromptLibrary
from analysis.retrieval.runner import RetrievalRunner
from analysis.scoring.service import TriggerScoringService
from analysis.settings import Settings
from analysis.models import utc_now
from analysis.validation import validate_record


class AnalysisPipeline:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ingestion = IngestionClient(settings)

    def _analysis_dir(self, brand_id: str) -> Path:
        return self._settings.data_dir / "brands" / brand_id / "analysis"

    def _load_facts(self, brand_id: str) -> list[dict[str, Any]]:
        return self._ingestion.load_facts(brand_id)

    def generate_prompts_only(self, brand_id: str) -> int:
        facts = self._load_facts(brand_id)
        prompts = PromptGenerator().generate(brand_id, facts)
        self._save_prompts(brand_id, prompts)
        return len(prompts)

    def run(self, brand_id: str) -> dict[str, Any]:
        batch_run_id = str(uuid4())
        facts = self._load_facts(brand_id)
        adir = self._analysis_dir(brand_id)

        prompts = PromptGenerator().generate(brand_id, facts)
        self._save_prompts(brand_id, prompts)

        runner = RetrievalRunner(facts)
        prompt_runs, all_fragments = self._run_retrieval(runner, prompts, batch_run_id)

        _write_jsonl(adir / "prompt_runs.jsonl", prompt_runs)
        _write_jsonl(adir / "response_fragments.jsonl", all_fragments)

        fragments_by_run = _group_fragments(all_fragments)
        extractor = TriggerExtractor()
        provenance_map = extractor.extract_all(prompt_runs, fragments_by_run, facts)
        raw_candidates = extractor.to_candidates(
            provenance_map,
            brand_id=brand_id,
            batch_run_id=batch_run_id,
            prompt_runs=prompt_runs,
            intent_by_prompt={p["prompt_id"]: p["intent_bucket"] for p in prompts},
        )

        scorer = TriggerScoringService(self._settings.scoring_config, facts)
        triggers = scorer.score(raw_candidates)
        self._save_triggers(brand_id, triggers)

        version = self._settings.scoring_config.get("version", "1.0.0")
        export_path = adir / "export" / "ranked_triggers.json"
        write_ranked_export(
            export_path,
            brand_id=brand_id,
            batch_run_id=batch_run_id,
            scoring_config_version=version,
            triggers=triggers,
        )

        batch_run = {
            "batch_run_id": batch_run_id,
            "brand_id": brand_id,
            "run_type": "analysis",
            "status": "completed",
            "started_at": utc_now(),
            "finished_at": utc_now(),
            "scoring_config_version": version,
            "stats": {
                "prompts": len(prompts),
                "prompt_runs": len(prompt_runs),
                "triggers": len(triggers),
            },
            "errors": [],
        }
        (adir / "batch_run.json").write_text(json.dumps(batch_run, indent=2))

        return {
            "brand_id": brand_id,
            "batch_run_id": batch_run_id,
            "prompts": len(prompts),
            "triggers": len(triggers),
            "export_path": str(export_path),
        }

    def rescore(self, brand_id: str) -> dict[str, Any]:
        adir = self._analysis_dir(brand_id)
        facts = self._load_facts(brand_id)
        triggers = _read_jsonl(adir / "triggers.jsonl")

        if not triggers:
            prompt_runs = _read_jsonl(adir / "prompt_runs.jsonl")
            prompts = PromptLibrary(adir / "prompts.jsonl").load()
            fragments = _read_jsonl(adir / "response_fragments.jsonl")
            batch_run_id = _batch_run_id(adir)
            fragments_by_run = _group_fragments(fragments)
            extractor = TriggerExtractor()
            provenance_map = extractor.extract_all(prompt_runs, fragments_by_run, facts)
            triggers = extractor.to_candidates(
                provenance_map,
                brand_id=brand_id,
                batch_run_id=batch_run_id,
                prompt_runs=prompt_runs,
                intent_by_prompt={p["prompt_id"]: p["intent_bucket"] for p in prompts},
            )

        scorer = TriggerScoringService(self._settings.scoring_config, facts)
        triggers = scorer.score(triggers)
        self._save_triggers(brand_id, triggers)

        batch_run_path = adir / "batch_run.json"
        batch_run = json.loads(batch_run_path.read_text()) if batch_run_path.exists() else {}
        batch_run_id = batch_run.get("batch_run_id", str(uuid4()))
        version = self._settings.scoring_config.get("version", "1.0.0")

        export_path = adir / "export" / "ranked_triggers.json"
        write_ranked_export(
            export_path,
            brand_id=brand_id,
            batch_run_id=batch_run_id,
            scoring_config_version=version,
            triggers=triggers,
        )

        if batch_run_path.exists():
            batch_run["scoring_config_version"] = version
            batch_run["stats"] = {**batch_run.get("stats", {}), "triggers": len(triggers)}
            batch_run_path.write_text(json.dumps(batch_run, indent=2))

        return {
            "brand_id": brand_id,
            "triggers": len(triggers),
            "export_path": str(export_path),
        }

    def _run_retrieval(
        self,
        runner: RetrievalRunner,
        prompts: list[dict[str, Any]],
        batch_run_id: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        prompt_runs: list[dict[str, Any]] = []
        all_fragments: list[dict[str, Any]] = []

        for prompt in prompts:
            run = runner.run_prompt(prompt)
            run["batch_run_id"] = batch_run_id
            fragments = run.pop("fragments", [])
            for frag in fragments:
                frag["prompt_run_id"] = run["prompt_run_id"]
                all_fragments.append(frag)
            prompt_runs.append(run)

        return prompt_runs, all_fragments

    def _save_prompts(self, brand_id: str, prompts: list[dict[str, Any]]) -> None:
        path = self._analysis_dir(brand_id) / "prompts.jsonl"
        PromptLibrary(path).save(prompts)
        for prompt in prompts:
            validate_record(prompt, "prompt.json", self._settings.schemas_dir)

    def _save_triggers(self, brand_id: str, triggers: list[dict[str, Any]]) -> None:
        path = self._analysis_dir(brand_id) / "triggers.jsonl"
        _write_jsonl(path, triggers)
        for trigger in triggers:
            validate_record(trigger, "trigger_candidate.json", self._settings.schemas_dir)


def _group_fragments(fragments: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for frag in fragments:
        run_id = frag.get("prompt_run_id", "")
        grouped.setdefault(run_id, []).append(frag)
    return grouped


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _batch_run_id(adir: Path) -> str:
    batch_path = adir / "batch_run.json"
    if batch_path.exists():
        return json.loads(batch_path.read_text()).get("batch_run_id", str(uuid4()))
    return str(uuid4())


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
