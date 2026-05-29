#!/usr/bin/env bash
# Run unit tests for all three sections (no live Tavily).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Section 1: backend-ingestion"
cd "$ROOT/backend-ingestion"
.venv/bin/pytest tests/ -q

echo "==> Section 2: backend-analysis"
cd "$ROOT/backend-analysis"
.venv/bin/pytest tests/ -q

echo "==> Section 3: frontend-dashboard"
cd "$ROOT/frontend-dashboard"
npm install --silent
npm run test
npm run build

echo "==> All stack tests passed"
