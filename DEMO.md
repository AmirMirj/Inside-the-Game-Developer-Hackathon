# DEMO — Judge walkthrough (≈ 5–6 minutes)

**Product:** Inside the Game — Synthetic Match Insights Engine  
**Data policy:** Synthetic football data only (no real Premier League feeds).

## Setup (before judges arrive)

**Terminal 1 — API**

```bash
cd services/insights-api
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Studio UI**

```bash
cd apps/studio-web
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Optional smoke (API must be up):

```bash
./scripts/demo.sh smoke
```

**UI defaults**

- Match: short sample `syn-northbridge-harbor-001` (fast) or half `syn-northbridge-harbor-half1`  
- Favorite club: `northbridge`  
- Player focus: `nb-9`

## Script

### 0:00 — Hook (30s)

> “Football stories don’t end with the scoreline. This Azure-shaped pipeline turns **synthetic** match events into explainable intelligence: ingest → interpret → explain → render → personalize — plus narrative recaps.”

Click **Start live** (speed ~12–50 for demo pace).

### 0:30 — Ingest + Interpret (60s)

- Point at **Event ticker** (Stage A) and **Match state** (Stage B).  
- Call out possession %, shots, pressure, rhythm updating from **code**, not the LLM.  
- Say: schemas + fixtures live under `data/synthetic/` — **synthetic only**.

### 1:30 — Explain + Render (90s)

- When an insight appears, show the overlay card (`match_clock`, priority, why it matters).  
- Note Stage C **ExplainAgent** (Azure when `.env` set; otherwise documented **mock** swap-in — `GET /api/v1/explain/provider`).  
- Stage D render contract is machine-readable for studio overlays.

### 3:00 — Personalize Fan vs Analyst (75s)

- Click **Prove Fan vs Analyst** (or wait for live personalization).  
- Side-by-side cards: **same moment**, different copy.  
- Change **Player focus** / **Favorite club** and re-run to show Stage E substance.

### 4:15 — Narrative + multi-language (60s)

- Click **Generate beats + recap**.  
- Toggle **EN → ES** — same arc, second language.  
- Call out ~60–90s read time on the recap card.

### 5:15 — Orchestration close (45s)

- Optionally show `POST /api/v1/matches/.../orchestrate` or `GET /api/v1/orchestrate/graph` in `/docs`.  
- Restate: multi-agent process (interpret → explain → narrative → personalize), Microsoft/Azure path, synthetic data, public GitHub + `ARCHITECTURE.md`.

## Backup path (if live stream/Azure fails)

1. **Load replay** timeline → click a clock chip → Fan/Analyst still compare.  
2. **Generate beats + recap** still works offline via mock explain.  
3. `EXPLAIN_PROVIDER=mock` is intentional for demos without keys.

## What judges should remember

1. Five-stage pipeline is real and visible in the UI.  
2. Explanations answer **why**, grounded in live state.  
3. Personalization changes **copy**, not only theme.  
4. Narratives ship in **EN + ES**.  
5. Orchestrator + CI make the agent design and engineering practices clear.
