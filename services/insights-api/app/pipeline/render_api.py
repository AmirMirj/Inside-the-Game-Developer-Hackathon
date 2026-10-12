"""HTTP routes for Stage D render payloads and replay timeline."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agents.explain_agent import ExplainAgent, get_explain_agent
from app.agents.llm import MockLlmClient
from app.models.insight import MatchInsight
from app.models.render import RenderPayload
from app.pipeline.explain import explain_event, scan_insights
from app.pipeline.ingest import resolve_events
from app.pipeline.render import insight_to_render, insights_to_timeline

router = APIRouter(tags=["render"])


@router.post("/render/from-insight", response_model=RenderPayload)
def render_from_insight(insight: MatchInsight) -> RenderPayload:
    """Shape a Stage C insight into a timed overlay payload."""
    return insight_to_render(insight)


@router.post("/matches/{match_id}/render/{seq}", response_model=RenderPayload)
def render_at_seq(
    match_id: str,
    seq: int,
    seed: int = Query(42),
) -> RenderPayload:
    events = resolve_events(match_id, seed=seed)
    try:
        insight = explain_event(events=events, seq=seq, agent=get_explain_agent())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return insight_to_render(insight)


@router.get("/matches/{match_id}/render/timeline", response_model=list[RenderPayload])
def render_timeline(
    match_id: str,
    seed: int = Query(42),
    min_priority: str = Query("medium", pattern="^(low|medium|high)$"),
    limit: int = Query(25, ge=1, le=100),
    use_mock: bool = Query(
        True,
        description="Use mock explain for fast deterministic timeline (recommended for UI)",
    ),
) -> list[RenderPayload]:
    events = resolve_events(match_id, seed=seed)
    agent: ExplainAgent = (
        ExplainAgent(client=MockLlmClient()) if use_mock else get_explain_agent()
    )
    insights = scan_insights(
        events,
        agent=agent,
        min_priority=min_priority,
        limit=limit,
    )
    return insights_to_timeline(insights)
