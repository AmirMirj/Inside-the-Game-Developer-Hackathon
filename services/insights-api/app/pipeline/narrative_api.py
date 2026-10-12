"""HTTP routes for Slice 6 narrative beats and recaps."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.narrative import MatchRecap, MultiLangRecap, StoryBeat
from app.pipeline.ingest import resolve_events
from app.pipeline.narrative import build_beats, build_multilang_recap, build_recap

router = APIRouter(tags=["narrative"])


@router.get("/matches/{match_id}/narrative/beats", response_model=list[StoryBeat])
def narrative_beats(
    match_id: str,
    seed: int = Query(42),
    language: str = Query("en", pattern="^(en|es)$"),
    min_priority: str = Query("medium", pattern="^(low|medium|high)$"),
    limit: int = Query(12, ge=1, le=40),
) -> list[StoryBeat]:
    events = resolve_events(match_id, seed=seed)
    try:
        return build_beats(
            events,
            language=language,
            min_priority=min_priority,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/matches/{match_id}/narrative/recap", response_model=MatchRecap)
def narrative_recap(
    match_id: str,
    seed: int = Query(42),
    language: str = Query("en", pattern="^(en|es)$"),
    min_priority: str = Query("medium", pattern="^(low|medium|high)$"),
    limit: int = Query(12, ge=1, le=40),
) -> MatchRecap:
    events = resolve_events(match_id, seed=seed)
    try:
        return build_recap(
            events,
            language=language,
            min_priority=min_priority,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/matches/{match_id}/narrative/recap/multilang",
    response_model=MultiLangRecap,
)
def narrative_recap_multilang(
    match_id: str,
    seed: int = Query(42),
    min_priority: str = Query("medium", pattern="^(low|medium|high)$"),
    limit: int = Query(12, ge=1, le=40),
) -> MultiLangRecap:
    """Same recap content arc in EN + ES for studio / global streaming demos."""
    events = resolve_events(match_id, seed=seed)
    try:
        return build_multilang_recap(
            events,
            languages=("en", "es"),
            min_priority=min_priority,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
