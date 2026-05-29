#!/usr/bin/env bash
# Quick ingestion smoke test (config + live Tavily call).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Run: cd backend-ingestion && python -m venv .venv && pip install -e '.[dev]'" >&2
  exit 1
fi
exec "$PYTHON" -m ingestion.cli test --live "$@"
