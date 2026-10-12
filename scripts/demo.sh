#!/usr/bin/env bash
# Judge-ready local demo helpers for Inside the Game.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="$ROOT/services/insights-api"
WEB="$ROOT/apps/studio-web"

usage() {
  cat <<EOF
Usage: ./scripts/demo.sh <command>

  api       Start insights API on :8000
  web       Start studio UI on :3000
  smoke     Hit health + orchestrate endpoints (API must be running)
  doctor    Print paths and quick checks

EOF
}

cmd="${1:-}"
case "$cmd" in
  api)
    cd "$API"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    export PYTHONPATH=.
    exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ;;
  web)
    cd "$WEB"
    exec npm run dev
    ;;
  smoke)
    echo "== health =="
    curl -sf http://127.0.0.1:8000/health | tee /dev/stderr | grep -q synthetic_only
    echo
    echo "== orchestrate graph =="
    curl -sf http://127.0.0.1:8000/api/v1/orchestrate/graph | head -c 200
    echo
    echo "== orchestrate sample =="
    curl -sf -X POST \
      "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/orchestrate?min_priority=low&insight_limit=3" \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print('steps:', [s['name'] for s in d['steps']]); print('insights:', len(d['insights'])); print('recap_en_s:', d['recap_en']['estimated_read_seconds'])"
    echo "OK"
    ;;
  doctor)
    echo "ROOT=$ROOT"
    echo "API venv: $API/.venv"
    test -d "$API/.venv" && echo "venv: present" || echo "venv: MISSING (cd services/insights-api && python -m venv .venv && pip install -r requirements.txt)"
    test -d "$WEB/node_modules" && echo "node_modules: present" || echo "node_modules: MISSING (cd apps/studio-web && npm install)"
    ;;
  *)
    usage
    exit 1
    ;;
esac
