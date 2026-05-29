# Trigger Discovery

> Collect brand knowledge with **Tavily**, simulate realistic user prompts, surface and rank high-intent **search triggers**, and review them in a dashboard before ad testing.

Trigger Discovery turns a single brand domain into a ranked, auditable list of keyword/phrase "triggers" you might want to advertise against. It crawls the brand's public web presence, normalizes the content into reusable facts, generates synthetic user prompts across intent buckets, retrieves the most relevant facts per prompt, extracts recurring phrases, scores them, and presents everything in a review UI with full source traceability.

Full product spec: [tavily-cursor-agent-plan.md](./tavily-cursor-agent-plan.md) · Work split: [TEAM.md](./TEAM.md)

---

## Table of contents

- [Architecture](#architecture)
- [How it works (end-to-end)](#how-it-works-end-to-end)
- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Running the full stack (3 terminals)](#running-the-full-stack-3-terminals)
- [One-command pipeline (no UI)](#one-command-pipeline-no-ui)
- [Offline demo (no Tavily / no API key)](#offline-demo-no-tavily--no-api-key)
- [Configuration](#configuration)
- [Service reference](#service-reference)
- [Data layout & contracts](#data-layout--contracts)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Architecture

Three independent services plus a shared contracts package:

```
                ┌──────────────────────┐
                │  frontend-dashboard  │   React + Vite UI  (:5173)
                │  brand setup · runs  │
                │  triggers · export   │
                └──────────┬───────────┘
                  calls    │   calls
          ┌────────────────┘   └────────────────┐
          ▼                                      ▼
┌──────────────────────┐              ┌──────────────────────┐
│   backend-ingestion  │  facts.jsonl │   backend-analysis   │
│  Tavily crawl/extract│─────────────▶│  prompts · retrieval │
│  normalize · KB API  │  (file/API)  │  triggers · scoring  │
│        (:8001)       │              │        (:8002)       │
└──────────┬───────────┘              └──────────┬───────────┘
           │            shared/ (JSON schemas,    │
           └───────────  scoring config,  ────────┘
                          fixtures)
                              │
                              ▼
                    data/brands/{brand_id}/...   (local, gitignored)
```

| Service | Stack | Port | Role |
|---------|-------|------|------|
| `backend-ingestion` | Python · FastAPI · Typer | `8001` | Tavily crawl/extract → normalized brand facts |
| `backend-analysis` | Python · FastAPI · Typer | `8002` | Synthetic prompts → retrieval → trigger scoring → export |
| `frontend-dashboard` | React 18 · Vite 5 · TypeScript | `5173` | Review UI: setup, run status, triggers, evidence, export |
| `shared` | JSON schemas + config + fixtures | — | Cross-team contracts (do not break without coordination) |

The two backends communicate primarily through the **shared `data/` directory** (same `DATA_DIR`). Analysis reads `data/brands/{id}/ingestion/normalized/facts.jsonl`; if the file isn't found it can fall back to the ingestion HTTP API.

---

## How it works (end-to-end)

1. **Ingestion** — Given a brand name + domain, Tavily Crawl discovers pages and Tavily Extract pulls structured content. Pages are classified (`homepage`, `product`, `pricing`, `docs`, `blog`, `comparison`, …), deduped, and normalized into `NormalizedFact` records (title, summary, features, pain points, competitor mentions, pricing terms, etc.).
2. **Prompt generation** — Analysis builds a library of synthetic user prompts across intent buckets (informational, commercial investigation, transactional, comparison, problem/solution, competitor-switching) from the brand facts. Optionally LLM-augmented.
3. **Retrieval** — Each prompt is run against an in-memory corpus built from the facts using **BM25** (default) or **embeddings**. The runner returns ranked response fragments with source-page traceability. (See `backend-analysis/src/analysis/retrieval/runner.py`.)
4. **Trigger extraction & scoring** — Recurring unigrams/bigrams/phrases are extracted, counted, and scored: `trigger_score = frequency + intent + relevance + distinctiveness − ambiguity`. Each trigger carries an `intent_bucket` and `recommended_action`.
5. **Export** — A stable `ranked_triggers.json` is written for the frontend.
6. **Review** — The dashboard shows crawl results, ranked triggers, and per-trigger evidence (which prompts/responses/pages produced it). Users approve/reject/flag and export a shortlist.

---

## Repository layout

```
cursor-hack/
├── shared/                  # JSON schemas, scoring config, demo fixtures
│   ├── schemas/             # brand, source_page, normalized_fact, prompt, trigger_candidate, ...
│   ├── config/scoring.default.json
│   └── fixtures/            # sample_brand.json, sample_facts.jsonl
├── backend-ingestion/       # Tavily crawl/extract, normalization, KB API (:8001)
├── backend-analysis/        # Prompts, retrieval, trigger scoring, export (:8002)
├── frontend-dashboard/      # Review UI (:5173)
├── data/                    # Local brand data (gitignored)
├── scripts/
│   ├── run-pipeline.sh      # ingest + analyze in one command
│   └── test-stack.sh        # run all tests across services
├── Makefile                 # install / dev / test shortcuts
├── docker-compose.yml       # optional containerized run
├── tavily-cursor-agent-plan.md
└── TEAM.md
```

---

## Prerequisites

- **Python** 3.9+ (3.11+ recommended)
- **Node** 20+ and npm
- A **Tavily API key** for live crawls (`TAVILY_API_KEY`). Not required for the offline/mock path — see [Offline demo](#offline-demo-no-tavily--no-api-key).

---

## Quick start

Install all dependencies (creates Python venvs per backend + installs npm packages):

```bash
# from repo root
make install
```

`make install` runs `pip install -e ".[dev]"` in each backend and `npm install` in the frontend. It assumes you've activated/created a venv per backend, or you can do it explicitly:

```bash
# Ingestion
cd backend-ingestion && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && cp .env.example .env && cd ..
# Analysis
cd backend-analysis  && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && cp .env.example .env && cd ..
# Frontend
cd frontend-dashboard && npm install && cp .env.example .env && cd ..
```

> Set `TAVILY_API_KEY` in `backend-ingestion/.env` for live crawls. Leave it blank (or set `TAVILY_MOCK=1`) to use mock responses.

---

## Running the full stack (3 terminals)

Run each service in its own terminal. Order doesn't strictly matter, but starting the backends first means the frontend has live data immediately.

```bash
# Terminal 1 — Ingestion API (:8001)
cd backend-ingestion && source .venv/bin/activate
python -m ingestion.cli serve
# (or without activating: .venv/bin/python -m ingestion.cli serve)

# Terminal 2 — Analysis API (:8002)
cd backend-analysis && source .venv/bin/activate
python -m analysis.cli serve

# Terminal 3 — Frontend (:5173)
cd frontend-dashboard
npm run dev
```

Then open **http://localhost:5173** (use `localhost`, not `127.0.0.1` — Vite binds to `localhost`).

Or use the Makefile shortcuts (each in its own terminal):

```bash
make dev-ingestion
make dev-analysis
make dev-frontend
```

**In the UI:** create a brand → it polls ingestion until the crawl completes → click **Run analysis** → view ranked triggers and drill into evidence → export your shortlist.

Quick health checks:

```bash
curl http://127.0.0.1:8001/docs            # ingestion (FastAPI docs)
curl http://127.0.0.1:8002/health          # analysis  → {"status":"ok","service":"analysis"}
curl http://localhost:5173                 # frontend
```

---

## One-command pipeline (no UI)

Ingest a brand and run the full analysis in a single step:

```bash
chmod +x scripts/run-pipeline.sh
./scripts/run-pipeline.sh "Acme" acme.com
# optional: competitors and seed topics (comma-separated)
./scripts/run-pipeline.sh "Acme" acme.com "rival.com,other.com" "analytics,funnels"
```

Equivalent manual steps:

```bash
# 1) Ingest (prints brand_id)
cd backend-ingestion && python -m ingestion.cli ingest --name "Acme" --domain acme.com

# 2) Analyze that brand
cd ../backend-analysis && python -m analysis.cli analyze --brand-id <brand_id>
```

The analysis step writes the frontend contract to:
`data/brands/{brand_id}/analysis/export/ranked_triggers.json`.

---

## Offline demo (no Tavily / no API key)

Seed the shared sample brand and analyze it without any external calls:

```bash
cd backend-analysis
python -m analysis.cli seed-fixture
python -m analysis.cli analyze --brand-id 00000000-0000-4000-8000-000000000001
python -m analysis.cli serve   # then browse the UI against this brand
```

You can also run the frontend fully mocked (no backends needed) by setting `VITE_USE_MOCK=true` in `frontend-dashboard/.env`.

---

## Configuration

Each service reads a local `.env` (copy from `.env.example`). Secrets and `data/` are gitignored.

### `backend-ingestion/.env`

| Var | Default | Description |
|-----|---------|-------------|
| `TAVILY_API_KEY` | — | Tavily key for live crawl/extract |
| `TAVILY_MOCK` | _(empty)_ | Any value forces mock responses (great for dev/tests) |
| `DATA_DIR` | `../data` | Shared brand data directory |
| `SHARED_SCHEMAS_DIR` | `../shared/schemas` | JSON schemas for validation |
| `CRAWL_MAX_DEPTH` | `2` | Tavily crawl depth |
| `CRAWL_LIMIT` | `30` | Max pages per crawl |
| `EXTRACT_DEPTH` | `basic` | Tavily extract depth |

### `backend-analysis/.env`

| Var | Default | Description |
|-----|---------|-------------|
| `DATA_DIR` | `../data` | Must match ingestion's `DATA_DIR` |
| `INGESTION_API_URL` | `http://127.0.0.1:8001` | Fallback when facts file is absent |
| `SHARED_SCHEMAS_DIR` | `../shared/schemas` | JSON schemas |
| `SCORING_CONFIG` | `../shared/config/scoring.default.json` | Versioned scoring weights |
| `RETRIEVAL_MODE` | `bm25` | `bm25` or `embeddings` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Used when `RETRIEVAL_MODE=embeddings` |
| `PROMPT_LLM_ENABLED` | `false` | Enable LLM-augmented prompt generation |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `PROMPT_LLM_MODEL` | — | LLM settings (falls back to templates) |

> Embeddings mode needs extra deps: `pip install -e ".[embeddings]"` in `backend-analysis`. Without them the runner cleanly falls back to BM25.

### `frontend-dashboard/.env`

| Var | Default | Description |
|-----|---------|-------------|
| `VITE_INGESTION_API_URL` | `http://127.0.0.1:8001` | Ingestion API base |
| `VITE_ANALYSIS_API_URL` | `http://127.0.0.1:8002` | Analysis API base |
| `VITE_USE_MOCK` | `false` | `true` serves built-in mock data (no backends needed) |

---

## Service reference

### Ingestion CLI (`python -m ingestion.cli`)

| Command | Description |
|---------|-------------|
| `test` | Verify `.env` / API key (add `--live` to hit Tavily once) |
| `ingest --name <n> --domain <d> [--competitors ..] [--topics ..]` | Full crawl + extract + normalize for one brand |
| `serve` | Start API on `:8001` (`--host 0.0.0.0` to expose) |

**Ingestion API (`:8001`)**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/brands` | Create brand + start ingestion (202; poll batch-run) |
| `GET` | `/brands` | List brands |
| `GET` | `/brands/{id}/batch-run` | Ingestion job status |
| `GET` | `/brands/{id}/facts` | Normalized facts |
| `GET` | `/brands/{id}/source-pages` | Crawl metadata |

### Analysis CLI (`python -m analysis.cli`)

| Command | Description |
|---------|-------------|
| `seed-fixture` | Copy shared fixtures into `data/` for offline demos |
| `list-brands` | Brands with ingestion facts available |
| `test [--brand-id <id>]` | Verify shared data dir + ingestion API health |
| `generate-prompts --brand-id <id>` | Build prompt library |
| `analyze --brand-id <id>` | Full batch: prompts → retrieval → triggers → export |
| `score --brand-id <id>` | Re-score triggers with current config |
| `run-pipeline --name <n> --domain <d>` | Ingest (Section 1) then analyze (Section 2) |
| `serve` | Start API on `:8002` |

**Analysis API (`:8002`)**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `GET` | `/brands/{id}/triggers` | Ranked export JSON (frontend contract) |
| `GET` | `/brands/{id}/prompt-runs` | Prompt run records |
| `GET` | `/brands/{id}/batch-run` | Latest analysis batch metadata |

### Frontend routes (`:5173`)

| Path | Screen |
|------|--------|
| `/` | Brand / project selector |
| `/brands/new` | Brand setup form |
| `/brands/:id` | Overview + crawl summary |
| `/brands/:id/runs` | Batch run status (polls ingestion + analysis) |
| `/brands/:id/knowledge` | Normalized facts / source pages |
| `/brands/:id/triggers` | Trigger ranking table + filters |
| `/brands/:id/triggers/:triggerId` | Trigger detail + source evidence |
| `/brands/:id/export` | Export / review handoff |

---

## Data layout & contracts

All shared entities are defined in `shared/schemas/` and use UUID v4 string IDs. On-disk layout per brand:

```
data/brands/{brand_id}/
  brand.json
  ingestion/
    raw/                       # raw Tavily extract
    normalized/facts.jsonl     # ← consumed by analysis
    source_pages.jsonl
    batch_run.json
  analysis/
    prompts.jsonl
    prompt_runs.jsonl
    response_fragments.jsonl
    triggers.jsonl
    batch_run.json
    export/ranked_triggers.json  # ← consumed by frontend
```

Core entities: `Brand`, `SourcePage`, `NormalizedFact`, `Prompt`, `PromptRun`, `ResponseFragment`, `TriggerCandidate`, `TriggerDecision`. **Do not change schema field names without coordinating** (see `shared/README.md` and `TEAM.md`).

---

## Testing

Run everything (Python unit tests for both backends + frontend vitest + build):

```bash
chmod +x scripts/test-stack.sh
./scripts/test-stack.sh
```

Or per service:

```bash
cd backend-ingestion && .venv/bin/pytest -q
cd backend-analysis  && .venv/bin/pytest -q
cd frontend-dashboard && npm run test      # vitest
cd frontend-dashboard && npm run build     # type-check + production build
```

`make test` runs both backend test suites.

---

## Troubleshooting

| Symptom | Likely cause & fix |
|---------|--------------------|
| Frontend shows unstyled / blank page | You opened `dist/index.html` directly, or used `http://127.0.0.1:5173`. Use the dev server at **`http://localhost:5173`** and hard-reload (`Cmd+Shift+R`). |
| `Address already in use` on `serve` | A service is already running on that port — that instance is fine, or kill it: `lsof -nP -iTCP:8002 -sTCP:LISTEN` then `kill <pid>`. |
| Analysis finds no facts | Ensure `DATA_DIR` matches ingestion's, and that `data/brands/{id}/ingestion/normalized/facts.jsonl` exists (run ingestion first, or `seed-fixture`). |
| Tavily errors / no key | Set `TAVILY_API_KEY`, or set `TAVILY_MOCK=1` for mock data. |
| `embeddings` mode import error | Install extras: `cd backend-analysis && pip install -e ".[embeddings]"` (otherwise it falls back to BM25). |
| `vite --host` crashes in restricted shells | Run plain `npm run dev` (binds to `localhost`); `--host` requires network-interface enumeration. |

---

## Optional: Docker

A scaffold `docker-compose.yml` is provided (Dockerfiles to be added per service):

```bash
TAVILY_API_KEY=... docker compose up
```

This brings up ingestion (`:8001`), analysis (`:8002`), and frontend (`:5173`) with `./data` and `./shared` mounted.
