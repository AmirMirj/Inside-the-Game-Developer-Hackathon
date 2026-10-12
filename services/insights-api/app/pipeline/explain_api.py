"""HTTP routes for Stage C explain / moments."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agents.explain_agent import get_explain_agent
from app.config import get_settings
from app.models.insight import CandidateMoment, MatchInsight
from app.pipeline.explain import detect_moments, explain_event, scan_insights
from app.pipeline.ingest import resolve_events

router = APIRouter(tags=["explain"])


@router.get("/explain/provider")
def explain_provider() -> dict:
    settings = get_settings()
    return {
        "configured_mode": settings.explain_provider,
        "active_provider": settings.resolve_explain_provider(),
        "azure_endpoint_set": bool(settings.azure_openai_endpoint),
        "azure_key_set": bool(settings.azure_openai_api_key),
        "deployment": settings.azure_openai_deployment,
    }


@router.get("/matches/{match_id}/moments", response_model=list[CandidateMoment])
def list_moments(
    match_id: str,
    seed: int = Query(42),
) -> list[CandidateMoment]:
    events = resolve_events(match_id, seed=seed)
    return [m for m, _, _ in detect_moments(events)]


@router.post("/matches/{match_id}/explain/{seq}", response_model=MatchInsight)
def explain_at_seq(
    match_id: str,
    seq: int,
    seed: int = Query(42),
) -> MatchInsight:
    events = resolve_events(match_id, seed=seed)
    try:
        return explain_event(events=events, seq=seq, agent=get_explain_agent())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/matches/{match_id}/insights/scan", response_model=list[MatchInsight])
def scan_match_insights(
    match_id: str,
    seed: int = Query(42),
    min_priority: str = Query("medium", pattern="^(low|medium|high)$"),
    limit: int = Query(20, ge=1, le=100),
) -> list[MatchInsight]:
    events = resolve_events(match_id, seed=seed)
    return scan_insights(
        events,
        agent=get_explain_agent(),
        min_priority=min_priority,
        limit=limit,
    )
