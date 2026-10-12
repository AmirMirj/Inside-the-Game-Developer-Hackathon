# AGENTS.md — Cursor / coding agent instructions

## Mission

Build **Inside the Game**: an Azure-backed five-stage pipeline that turns **synthetic** football events into explainable, renderable, personalized match intelligence.

## Always do

1. Read `SPEC.md` and the **next open slice** in `FEATURES.md` before coding.  
2. Prefer vertical slices that demo a stage end-to-end.  
3. Keep stats/aggregation **deterministic**; use LLMs for explanation, narrative, and personalization.  
4. Validate events/insights against `packages/schemas`.  
5. Label all demo data as synthetic in UI copy and docs.  
6. Update acceptance checkboxes in `FEATURES.md` when a slice is done.  

## Never do

- Use or import real Premier League match datasets  
- Commit `.env`, API keys, or cloud secrets  
- Skip Stage C “why it matters” in favor of raw metrics only  
- Build personalization that only changes theme colors  
- Expand scope into stretch items before slices 1–6 meet criteria  

## Stack conventions

- API: FastAPI under `services/insights-api`  
- Agents: `MatchIntelligenceOrchestrator` wires Interpret → Explain → Narrative → Personalize (`app/agents/orchestrator.py`); Azure OpenAI via swap-in LLM client  
- UI: Next.js App Router under `apps/studio-web`  
- Schemas: JSON Schema is source of truth; codegen optional  
- Demo: follow `DEMO.md`; smoke with `./scripts/demo.sh smoke` when API is up

## Output quality bar

- Typed models for events, match state, insights, viewer profiles  
- Small focused modules per pipeline stage  
- Tests for interpret/aggregation on fixed fixtures  
- Docs stay truthful to what the code actually does  

## When unsure

Ask: “Does this help the five-stage demo for Fan vs Analyst on one live synthetic match?” If no, defer.
