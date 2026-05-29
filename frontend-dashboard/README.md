# Frontend — Review Dashboard (Engineer 3)

React + Vite UI for brand setup, run status, knowledge overview, trigger ranking, and export.

## Quick start

```bash
cd frontend-dashboard
npm install
cp .env.example .env
npm run dev   # http://localhost:5173
```

Requires ingestion API (`:8001`) and analysis API (`:8002`) for live data, or set `VITE_USE_MOCK=true`.

## Wired flows

| Page | APIs |
|------|------|
| New brand | `POST /brands` (ingestion) → `/brands/:id/runs` |
| Run status | Poll `GET .../batch-run` on ingestion + analysis; `POST .../analyze` |
| Overview / Knowledge | `GET /facts`, `GET /source-pages` |
| Triggers / Detail / Export | `GET /triggers`, `GET /prompt-runs` |

```bash
cp .env.example .env
npm run dev
npm run test
```

## Routes

| Path | Screen |
|------|--------|
| `/` | Brand / project selector |
| `/brands/new` | Brand setup |
| `/brands/:id` | Brand overview + crawl summary |
| `/brands/:id/runs` | Batch run status |
| `/brands/:id/knowledge` | Normalized facts / source pages |
| `/brands/:id/triggers` | Trigger ranking table |
| `/brands/:id/triggers/:triggerId` | Trigger detail + evidence |
| `/brands/:id/export` | Export / review handoff |

## API contracts

See `src/api/client.ts` and `src/types/contracts.ts` (mirror `shared/schemas`).

## Definition of done

- [ ] Create/open brand project
- [ ] Crawl progress + ingestion results
- [ ] Ranked triggers with evidence drill-down
- [ ] Approve/reject/flag decisions + export shortlist
