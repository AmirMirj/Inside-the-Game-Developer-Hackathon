"""HTTP entry for the multi-agent orchestrator (Slice 7)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agents.orchestrator import MatchIntelligenceOrchestrator
from app.pipeline.ingest import resolve_events

router = APIRouter(tags=["orchestrator"])


@router.post("/matches/{match_id}/orchestrate")
def orchestrate_match(
    match_id: str,
    seed: int = Query(42),
    min_priority: str = Query("medium", pattern="^(low|medium|high)$"),
    insight_limit: int = Query(12, ge=1, le=40),
    include_recap: bool = Query(True),
) -> dict:
    """
    Run Interpret → Explain → Narrative → Personalize (+ multilang recap).

    Returns a judge-friendly summary of agent steps and artifacts.
    """
    events = resolve_events(match_id, seed=seed)
    try:
        result = MatchIntelligenceOrchestrator().run(
            events,
            min_priority=min_priority,
            insight_limit=insight_limit,
            include_recap=include_recap,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.to_dict()


@router.get("/orchestrate/graph")
def orchestrate_graph() -> dict:
    """Static agent graph for docs / demo slides."""
    return {
        "pattern": "semantic_kernel_style_process",
        "data_policy": "synthetic_only",
        "nodes": [
            {"id": "ingest", "type": "source", "module": "pipeline.ingest"},
            {"id": "interpret", "type": "deterministic", "module": "pipeline.interpret"},
            {"id": "detect", "type": "rules", "module": "pipeline.moments"},
            {"id": "explain", "type": "agent", "module": "agents.explain_agent"},
            {"id": "narrative", "type": "agent", "module": "agents.narrative_agent"},
            {"id": "personalize", "type": "agent", "module": "agents.personalize_agent"},
            {"id": "render", "type": "contract", "module": "pipeline.render"},
        ],
        "edges": [
            ["ingest", "interpret"],
            ["interpret", "detect"],
            ["detect", "explain"],
            ["explain", "narrative"],
            ["explain", "personalize"],
            ["explain", "render"],
            ["personalize", "render"],
        ],
    }
