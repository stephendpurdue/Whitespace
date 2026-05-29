# Backend — Analysis (Engineer 2)

Synthetic prompts, corpus retrieval, trigger extraction, and scoring.

## Quick start

```bash
cd backend-analysis
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m analysis.cli seed-fixture
python -m analysis.cli analyze --brand-id 00000000-0000-4000-8000-000000000001
```

## Depends on Engineer 1 (wired)

Reads `data/brands/{brand_id}/ingestion/normalized/facts.jsonl` from the **same `DATA_DIR`** as ingestion (`../data` by default), or falls back to ingestion API `http://127.0.0.1:8001`.

```bash
python -m analysis.cli list-brands    # brands ready for analysis
python -m analysis.cli test           # verify shared data dir
python -m analysis.cli run-pipeline --name "Acme" --domain acme.com  # ingest + analyze
```

Use `seed-fixture` to copy `shared/fixtures/sample_facts.jsonl` for offline demos.

## CLI commands

| Command | Description |
|---------|-------------|
| `seed-fixture` | Copy shared fixtures into `data/` |
| `generate-prompts` | Build prompt library from brand facts |
| `analyze` | Full batch: prompts → retrieval → triggers → export |
| `score` | Re-score triggers with current config |
| `serve` | Local API on port 8002 |

## Retrieval modes

- `RETRIEVAL_MODE=bm25` (default) — `rank-bm25` over normalized facts
- `RETRIEVAL_MODE=embeddings` — requires `pip install -e ".[embeddings]"`

## Optional LLM prompts

Set `PROMPT_LLM_ENABLED=true` and `OPENAI_API_KEY`. Falls back to templates on failure.

## API (port 8002)

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Service health |
| `GET /brands/{id}/triggers` | Ranked export JSON |
| `GET /brands/{id}/prompt-runs` | Prompt run records |
| `GET /brands/{id}/batch-run` | Latest analysis batch metadata |

## Outputs

- `analysis/prompts.jsonl`
- `analysis/prompt_runs.jsonl`
- `analysis/response_fragments.jsonl`
- `analysis/triggers.jsonl`
- `analysis/batch_run.json`
- `analysis/export/ranked_triggers.json` (frontend contract)

## Definition of done

- [x] Batch prompts against one brand corpus
- [x] Ranked triggers with traceability (prompts, pages, responses)
- [x] Stable export JSON for frontend
