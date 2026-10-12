"""HTTP routes for Stage B live match state."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.state import MatchState
from app.pipeline.ingest import resolve_events
from app.pipeline.interpret import build_state

router = APIRouter(tags=["interpret"])


@router.get("/matches/{match_id}/state", response_model=MatchState)
def get_match_state(
    match_id: str,
    up_to_seq: int | None = Query(
        None,
        ge=0,
        description="If set, apply events with seq <= up_to_seq only",
    ),
    seed: int = Query(42),
) -> MatchState:
    events = resolve_events(match_id, seed=seed)
    if up_to_seq is not None:
        events = [e for e in events if e.seq <= up_to_seq]
    if not events:
        raise HTTPException(status_code=404, detail="No events to interpret")
    return build_state(match_id, events)


@router.get("/matches/{match_id}/state/at/{seq}", response_model=MatchState)
def get_match_state_at_seq(
    match_id: str,
    seq: int,
    seed: int = Query(42),
) -> MatchState:
    events = [e for e in resolve_events(match_id, seed=seed) if e.seq <= seq]
    if not events:
        raise HTTPException(status_code=404, detail="No events at or before seq")
    return build_state(match_id, events)
