# Backend — Ingestion (Engineer 1)

Tavily crawl/extract, normalization, and brand knowledge base storage.

## Quick start

```bash
cd backend-ingestion
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set TAVILY_API_KEY
```

## Test command (API key + Tavily)

Config only (no API credits):

```bash
python -m ingestion.cli test
```

Full smoke test (calls Tavily once):

```bash
python -m ingestion.cli test --live
# or
./scripts/test.sh
```

From repo root:

```bash
./backend-ingestion/scripts/test.sh
```

Then ingest a brand:

```bash
python -m ingestion.cli ingest --name "Acme" --domain acme.com
```

## CLI commands

| Command | Description |
|---------|-------------|
| `test` | Verify `.env` / API key (`--live` hits Tavily) |
| `ingest` | Full crawl + extract + normalize for one brand |
| `serve` | Local API on port 8001 |

## Outputs

Writes under `../data/brands/{brand_id}/ingestion/` per `shared/README.md`.

## Interface for Engineer 2

- `GET /brands/{brand_id}/facts` — normalized facts
- `GET /brands/{brand_id}/source-pages` — crawl metadata
- Files: `normalized/facts.jsonl`, `source_pages.jsonl`

## API (port 8001)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/brands` | Create brand + start ingestion (202, poll batch-run) |
| `GET` | `/brands/{id}/batch-run` | Ingestion job status |
| `GET` | `/brands/{id}/facts` | Normalized facts JSONL as array |
| `GET` | `/brands/{id}/source-pages` | Source pages |

```bash
ingestion serve
curl -X POST http://127.0.0.1:8001/brands \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme","primary_domain":"acme.com"}'
```

## Definition of done

- [x] One command ingests a brand from domain (`ingestion ingest` or `POST /brands`)
- [x] Pages classified (`page_type`)
- [x] Normalized facts queryable without manual cleanup
- [x] Rerunnable ingestion job with dedup + traceability
