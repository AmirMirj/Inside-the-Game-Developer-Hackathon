# SPEC — Inside the Game

**Challenge:** The Synthetic Match Insights Engine for Premier League Studio  
**Hackathon:** Inside the Game (Microsoft × Premier League)  
**Constraint:** Synthetic, football-realistic data only — no real Premier League match data.

## Problem

Match coverage still leans on scores and raw stats. Studios, streamers, and fans need **explainable match intelligence**: what happened, why it matters, and how to experience it in a mode that fits them — in real time and after the whistle.

## Vision

**Inside the Game** is an Azure-hosted AI insights engine that turns a live stream of synthetic football events into:

1. Aggregated match states and meaningful stats  
2. Explained key moments (not just event logs)  
3. Narratives and automated recaps  
4. Studio-ready, timed outputs for on-screen storytelling  
5. Personalized views for casual fans, analysts, and broadcast/studio roles  

## Target users

| Persona | Need |
|---------|------|
| **Casual fan** | Plain-language story, favorite club/player focus, optional language |
| **Analyst** | Density, patterns, pressure/rhythm, pass quality, machine-readable metrics |
| **Studio / broadcast** | Timed, overlay-friendly insights synced to match clock |

## Success for demo (definition of done)

Judges can watch one synthetic match feed and see:

1. Events ingested live (pipeline stage A)  
2. Stats/state updating in real time (B)  
3. At least one **explained** key moment with “why it matters” (C)  
4. On-screen / studio-panel rendering of that insight (D)  
5. The **same moment** shown differently for Fan vs Analyst (E)  
6. A short automated recap + optional second language  
7. Clear Microsoft AI / Azure usage (agents + model calls)

## Non-goals (hackathon)

- Real Premier League proprietary datasets or licensed broadcast video  
- Full production graphics-engine integration with a real renderer partner  
- Perfect CV auto-eventing from video (optional stretch; synthetic events are the primary source)  
- Every metric in the brief — prefer depth on the five-stage pipeline

## Mandatory pipeline (five stages)

| Stage | Requirement |
|-------|-------------|
| **A — Ingest** | Synthetic match events as they happen (passes, shots, tackles, possession, pressure, metadata) |
| **B — Interpret** | Meaningful stats, patterns, and context |
| **C — Explain** | Why a moment matters (control vs chaos, pressure, rhythm) |
| **D — Render** | Studio/on-screen suitable, timed, preferably machine-readable for overlays |
| **E — Personalize** | Distinct experiences (e.g. favorite club/player, fan vs analyst modes) |

## Judging alignment

| Criterion (20% each) | How this project addresses it |
|----------------------|-------------------------------|
| Technological implementation | Clean pipeline modules, schemas, CI, docs, Azure stack |
| Agentic design & innovation | Multi-agent orchestration (interpret / explain / narrative / personalize) |
| Real-world impact | Studio + fan personalization path, production-shaped outputs |
| UX & presentation | Live studio console + demo narrative |
| Category adherence | Synthetic data → explainable intelligence → narratives → personalization |

## Hero technologies (Microsoft)

- **Azure OpenAI** / Azure AI Foundry models for explanation & narrative  
- **Semantic Kernel** (or Azure AI Agents) for agent orchestration  
- **Azure** hosting path (Functions / Container Apps / App Service — pick one for demo)  
- Optional: Azure Event Hubs / Service Bus if streaming needs scale; for hackathon, in-process + WebSocket/SSE is acceptable if documented as the Azure-shaped design

## Data policy

- All match events are **synthetic** and football-realistic  
- Schemas and generators live in-repo under `data/synthetic/`  
- Never import or redistribute real PL match feeds

## Product principles

1. **Explain > list** — every highlighted moment answers “so what?”  
2. **One pipeline, many lenses** — same intelligence, different personalization  
3. **Live-capable** — ingest and insight latency fit a match clock demo  
4. **Studio-shaped** — outputs have `match_clock`, `priority`, and render payload  
5. **Spec-driven** — implement only slices in `FEATURES.md`; update the spec when scope changes
