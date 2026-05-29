# Three-person work split

## Engineer 1 — Ingestion (`backend-ingestion/`)

**Owns:** Tavily integration, crawl/extract jobs, normalization, `data/.../ingestion/`, port 8001 API.

**First tasks:**
1. Implement `tavily_client.py` (Crawl + Extract)
2. Page type classifier (homepage, product, pricing, etc.)
3. Enrich `normalization/pipeline.py` (facts extraction)
4. `POST /brands` for frontend-driven ingest

**Hands off to Engineer 2:** `facts.jsonl`, `source_pages.jsonl`

---

## Engineer 2 — Analysis (`backend-analysis/`)

**Owns:** Prompt generator, retrieval runner, trigger extraction, scoring, export JSON, port 8002 API.

**First tasks:**
1. Improve `prompts/generator.py` (templates + LLM optional)
2. Replace keyword retrieval with embeddings/BM25
3. Entity/keyphrase extraction in `extraction/`
4. Attach `intent_bucket` per trigger from prompt runs

**Hands off to Engineer 3:** `analysis/export/ranked_triggers.json`

**Depends on:** Engineer 1 facts available (file or API).

---

## Engineer 3 — Frontend (`frontend-dashboard/`)

**Owns:** Routes, tables, filters, trigger detail, decisions, export UX.

**First tasks:**
1. Brand setup form → ingestion API
2. Run status polling from `batch_run.json`
3. Wire all pages to live APIs (disable mock)
4. Prompt-run table + source evidence drill-down

**Depends on:** Stable schemas in `shared/` and ranked export from Engineer 2.

---

## Shared (`shared/`) — coordinate before merging

- Schema changes require review from all three
- Version `scoring.default.json` when weights change
- Add sample fixture data under `shared/fixtures/` for integration demos
