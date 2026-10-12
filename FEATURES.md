# FEATURES — Ordered slices

Implement **top to bottom**. Do not start a later slice until the previous slice meets its acceptance criteria. Stretch items are optional.

---

## Slice 0 — Workspace & contracts

**Goal:** Runnable repo skeleton with shared event schema and empty pipeline stages.

**Acceptance criteria**

- [x] Spec docs present (`SPEC.md`, `FEATURES.md`, `ARCHITECTURE.md`, `DEMO.md`)  
- [x] Shared event schema validates sample synthetic events  
- [x] Pipeline stage packages/folders exist for A→E  
- [x] README explains how to run locally  
- [x] Insights API boots and serves fixture events (`/api/v1/matches/...`)  
- [x] Next.js studio app scaffolded (can wait until Slice 4 if API-first)

---

## Slice 1 — Synthetic ingest (Stage A)

**Goal:** Emit a live stream of football-realistic synthetic events.

**Acceptance criteria**

- [x] Generator produces passes, shots, tackles, possession changes, pressure events + match metadata  
- [x] Events include `event_id`, `match_id`, `match_clock`, `type`, `actors`, `payload`, `timestamp`  
- [x] Client can subscribe via WebSocket or SSE and see events arrive in order  
- [x] At least one full 5–10 minute accelerated “half” sample for demos  

**How to try:** match `syn-northbridge-harbor-half1`, SSE `/api/v1/matches/{id}/stream?speed=6` (~7.5 min wall), or WS `/api/v1/matches/{id}/ws?speed=6`.

---

## Slice 2 — Interpret & match state (Stage B)

**Goal:** Aggregate events into live stats and football state.

**Acceptance criteria**

- [x] Running possession %, shot counts, pass counts/accuracy (where data allows)  
- [x] Simple pressure / rhythm indicators derived from recent event windows  
- [x] Pass quality fields when present: distance, accuracy flag, difficulty rating  
- [x] State API or stream update after each relevant event  
- [x] Unit tests or golden fixtures for aggregation on a fixed synthetic sequence  

**How to try:** `GET /api/v1/matches/{id}/state` · live ticks: `.../stream?include_state=true`

---

## Slice 3 — Explain key moments (Stage C)

**Goal:** Detect moments and explain *why they matter* via an Azure-backed agent.

**Acceptance criteria**

- [x] Detector flags candidate moments (e.g. shot, big pressure swing, turnover in dangerous area)  
- [x] Explain agent returns structured insight: headline, why_it_matters, evidence[], confidence  
- [x] Explanation references match context (score/state), not only the raw event  
- [x] Uses Azure OpenAI / Foundry (or documented mock with swap-in client)  

**How to try:** `GET .../moments` · `POST .../explain/{seq}` · `POST .../insights/scan` · stream `include_insights=true`  
**Provider:** set `AZURE_OPENAI_*` in `.env`, or leave blank for mock (`GET /api/v1/explain/provider`).

---

## Slice 4 — Studio render outputs (Stage D)

**Goal:** Timed, machine-readable insight payloads suitable for on-screen / studio panel.

**Acceptance criteria**

- [x] Render schema includes `match_clock`, `duration_ms`, `priority`, `overlay_type`, `text`, `entities`  
- [x] Studio UI shows live events + current insight card synced to match clock  
- [x] Insights can be replayed along the demo timeline  

**How to try:** API `GET .../render/timeline` · UI `cd apps/studio-web && npm install && npm run dev` → http://localhost:3000

---

## Slice 5 — Personalization (Stage E)

**Goal:** Same underlying intelligence, two genuinely different experiences.

**Acceptance criteria**

- [x] Viewer profile: role (`fan` | `analyst` | `studio`), language, favorite club, favorite player(s), optional focus mode  
- [x] Personalize agent/transform rewrites copy + emphasis (not just CSS)  
- [x] Side-by-side or mode toggle in UI proves Fan vs Analyst difference on one moment  
- [x] Player-focused mode biases narratives toward selected player when involved  

**How to try:** `POST .../personalize/{seq}/compare` · UI button **Prove Fan vs Analyst** (side-by-side cards)

---

## Slice 6 — Narratives & recap

**Goal:** Key narratives during play + automated post-segment recap.

**Acceptance criteria**

- [x] Narrative agent produces short in-match story beats from explained moments  
- [x] End-of-demo recap (60–90s read) with milestones and player context  
- [x] Multi-language: at least **EN + one other** (e.g. ES, DE, FR, AR) for the same recap  

**How to try:** `GET .../narrative/beats` · `GET .../narrative/recap/multilang` · UI **Generate beats + recap** (EN/ES toggle)

---

## Slice 7 — Agentic orchestration & polish

**Goal:** Clear multi-agent design for judges; CI + docs.

**Acceptance criteria**

- [x] Orchestrator wires Interpret → Explain → Narrative → Personalize (SK / Azure Agents)  
- [x] Architecture diagram or sequence in `ARCHITECTURE.md` matches code  
- [x] GitHub Actions: lint/test on PR  
- [x] Public README + `DEMO.md` walkthrough ready for judges  

**How to try:** `POST /api/v1/matches/{id}/orchestrate` · `GET /api/v1/orchestrate/graph` · `./scripts/demo.sh smoke` · `DEMO.md`

---

## Stretch (only if slices 1–6 are solid)

| ID | Idea |
|----|------|
| S1 | Speed/distance thresholds → player callouts |
| S2 | Ball/shot speed metrics in synthetic payloads |
| S3 | “Auto-eventing” stub: video frame → event (mocked model) |
| S4 | Azure Event Hubs path for ingest |
| S5 | More languages / market packs |
| S6 | Overlay JSON export matching a fictional renderer partner contract |

---

## Explicitly deferred

- Real PL data  
- Full CV pipeline training  
- Native broadcast graphics engine plugins
