#!/usr/bin/env bash
# Section 1 (ingest) + Section 2 (analyze) for one brand.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

NAME="${1:?Usage: ./scripts/run-pipeline.sh \"Brand Name\" domain.com}"
DOMAIN="${2:?}"
COMPETITORS="${3:-}"
TOPICS="${4:-}"

INGEST_PY="${ROOT}/backend-ingestion/.venv/bin/python"
ANALYSIS_PY="${ROOT}/backend-analysis/.venv/bin/python"
[[ -x "$INGEST_PY" ]] || INGEST_PY="python3"
[[ -x "$ANALYSIS_PY" ]] || ANALYSIS_PY="python3"

INGEST_ARGS=(--name "$NAME" --domain "$DOMAIN")
[[ -n "$COMPETITORS" ]] && INGEST_ARGS+=(--competitors "$COMPETITORS")
[[ -n "$TOPICS" ]] && INGEST_ARGS+=(--topics "$TOPICS")

echo "==> Section 1: ingestion"
INGEST_JSON="$("$INGEST_PY" -m ingestion.cli ingest "${INGEST_ARGS[@]}" 2>&1)"
echo "$INGEST_JSON"
BRAND_ID="$(echo "$INGEST_JSON" | "$ANALYSIS_PY" -c "import sys,json; print(json.load(sys.stdin)['brand_id'])")"

echo "==> Section 2: analysis (brand_id=$BRAND_ID)"
cd "$ROOT/backend-analysis"
exec "$ANALYSIS_PY" -m analysis.cli analyze --brand-id "$BRAND_ID"
