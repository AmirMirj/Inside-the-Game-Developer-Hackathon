# Inside the Game

**Synthetic Match Insights Engine for Premier League Studio**  
Microsoft × Premier League hackathon — AI that turns synthetic football events into explainable match intelligence, real-time narratives, and personalized studio/fan experiences.

> **Data policy:** Synthetic, football-realistic data only. No real Premier League match data.

## Spec-driven development

| Doc | Purpose |
|-----|---------|
| [SPEC.md](./SPEC.md) | Problem, users, success criteria, non-goals |
| [FEATURES.md](./FEATURES.md) | Ordered implementation slices + acceptance criteria |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Pipeline, Azure mapping, contracts |
| [STUDYGUIDE.md](./STUDYGUIDE.md) | One-page 80/20 + schematics (learn / pitch) |
| [DEMO.md](./DEMO.md) | Judge walkthrough |
| [AGENTS.md](./AGENTS.md) | Instructions for coding agents (Cursor) |

**Rule:** implement only the next unchecked slice in `FEATURES.md`.

## Five-stage pipeline

1. **Ingest** synthetic match events  
2. **Interpret** into stats, patterns, context  
3. **Explain** why moments matter  
4. **Render** timed studio / overlay outputs  
5. **Personalize** for fan, analyst, and studio modes  

## Deploy on Vercel (multi-service)

This repo uses [Vercel Services](https://vercel.com/docs/services): Next.js UI + FastAPI in one project via root [`vercel.json`](./vercel.json).

1. Push `vercel.json` to `main`.
2. In Vercel → **Import** `AmirMirj/Inside-the-Game-Developer-Hackathon`.
3. Keep **Services** / multi-service (do not pick a single folder unless you only want the UI).
4. Deploy. UI is `/`; API is `/api/v1/...`, `/health`, `/docs`.
5. Optional env on the project: `AZURE_OPENAI_*` / `EXPLAIN_PROVIDER` for live Azure explain.

**Note:** Long SSE streams can hit serverless limits — for demos use the short match + high stream speed, or **Load replay** / **Prove Fan vs Analyst** / **Generate beats + recap**.

## Judge quick start

```bash
# API
./scripts/demo.sh doctor   # optional checks
cd services/insights-api && source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# UI (second terminal)
cd apps/studio-web && npm run dev
# → http://localhost:3000

# Walkthrough: DEMO.md
# Full agent run:
curl -s -X POST "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/orchestrate?min_priority=low" | jq '.steps'
```

## Stack (hackathon default)

- **API:** Python · FastAPI · Semantic Kernel–style orchestrator · Azure OpenAI (mock fallback)  
- **UI:** TypeScript · Next.js (studio console)  
- **Contracts:** JSON Schema in `packages/schemas`  
- **CI:** GitHub Actions (API lint/tests + studio typecheck/build)  

## Repo layout

```text
apps/studio-web/          Studio UI
services/insights-api/    Ingest, state, agents, render API
packages/schemas/         Shared event & insight contracts
data/synthetic/           Generators + fixtures
```

## Quick start

```bash
cd services/insights-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### Slice 1 — live synthetic ingest

| Match id | What |
|----------|------|
| `syn-northbridge-harbor-001` | Short fixture |
| `syn-northbridge-harbor-half1` | Full synthetic first half (~45′ clock → ~7.5′ wall at `speed=6`) |

```bash
# List matches
curl -s http://127.0.0.1:8000/api/v1/matches | jq

# SSE stream (accelerated half)
curl -N "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/stream?speed=6"

# WebSocket (example with websocat if installed)
# websocat "ws://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/ws?speed=6"
```

`speed` = match-clock seconds per wall-clock second. Use `speed=10000` for a fast dry run.

### Slice 2 — live match state

```bash
# Snapshot after all events
curl -s http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/state | jq

# State up to a sequence number
curl -s "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/state?up_to_seq=50" | jq

# Stream events + state together
curl -N "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/stream?speed=6&include_state=true"
```

### Slice 3 — explain key moments

```bash
# Which LLM backend is active (mock until Azure env is set)
curl -s http://127.0.0.1:8000/api/v1/explain/provider | jq

# Detected moments (no LLM)
curl -s http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/moments | jq

# Explain one moment (mock or Azure)
SEQ=$(curl -s http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/moments | jq '.[0].event_seq')
curl -s -X POST "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/explain/$SEQ" | jq

# Stream with state + insights
curl -N "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/stream?speed=10000&include_state=true&include_insights=true"
```

Copy `services/insights-api/.env.example` → `.env` and set `AZURE_OPENAI_*` to use Azure; otherwise the **mock** client runs. Never commit keys.

### Slice 4 — studio render + UI

```bash
# Timed overlay timeline
curl -s "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/render/timeline?use_mock=true" | jq

# Studio console
cd apps/studio-web && npm install && npm run dev
# → http://localhost:3000
```

In the UI: **Start live** for SSE events/state/overlays, or **Load replay timeline** to scrub insights by match clock.

### Slice 5 — Fan vs Analyst personalization

```bash
# Default viewer profiles
curl -s http://127.0.0.1:8000/api/v1/personalize/profiles/defaults | jq

# Same moment, two voices
SEQ=$(curl -s http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/moments | jq '.[0].event_seq')
curl -s -X POST "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/personalize/$SEQ/compare?player_focus=nb-9" | jq
```

In the UI: set **Favorite club** / **Player focus**, then click **Prove Fan vs Analyst** for side-by-side copy.

### Slice 6 — narratives & multi-language recap

```bash
# In-match story beats
curl -s "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/narrative/beats?language=en" | jq '.[0]'

# Same recap arc in EN + ES
curl -s "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-half1/narrative/recap/multilang" | jq '.recaps | keys, .en.estimated_read_seconds, .es.title'
```

In the UI: **Generate beats + recap**, then switch **EN/ES**.

### Slice 7 — orchestration & polish

```bash
# Agent graph (for slides / judges)
curl -s http://127.0.0.1:8000/api/v1/orchestrate/graph | jq

# One-shot pipeline: interpret → explain → narrative → personalize (+ EN/ES recap)
curl -s -X POST \
  "http://127.0.0.1:8000/api/v1/matches/syn-northbridge-harbor-001/orchestrate?min_priority=low&insight_limit=5" \
  | jq '{steps, insights:(.insights|length), fan:(.personalized.fan|length), recap_en_s:.recap_en.estimated_read_seconds}'
```

CI runs API **ruff + pytest** and studio **tsc + next build** on every PR. Follow **[DEMO.md](./DEMO.md)** for the live walkthrough.

## Hackathon tags

Integrating AI and CI · Process improvement · Innovation of football statistics · Real-time football analysis
