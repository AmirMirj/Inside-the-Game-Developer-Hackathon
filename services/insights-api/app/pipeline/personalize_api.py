"""HTTP routes for Stage E personalization."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.insight import MatchInsight
from app.models.profile import ViewerProfile
from app.models.render import RenderPayload
from app.models.state import MatchState
from app.pipeline.explain import explain_event
from app.pipeline.ingest import resolve_events
from app.pipeline.interpret import MatchStateEngine
from app.pipeline.personalize import (
    compare_fan_analyst,
    default_profiles,
    personalize_insight,
)

router = APIRouter(tags=["personalize"])


class PersonalizeRequest(BaseModel):
    insight: MatchInsight
    profile: ViewerProfile
    state: MatchState | None = None


class CompareRequest(BaseModel):
    insight: MatchInsight
    state: MatchState | None = None
    fan: ViewerProfile | None = None
    analyst: ViewerProfile | None = None


class CompareResponse(BaseModel):
    fan: RenderPayload
    analyst: RenderPayload


class CompareAtSeqRequest(BaseModel):
    fan: ViewerProfile | None = None
    analyst: ViewerProfile | None = None
    favorite_club_id: str | None = Field(default="northbridge")
    player_focus: str | None = Field(default="nb-9")


@router.get("/personalize/profiles/defaults")
def get_default_profiles() -> dict:
    return {k: v.model_dump() for k, v in default_profiles().items()}


@router.post("/personalize", response_model=RenderPayload)
def personalize(req: PersonalizeRequest) -> RenderPayload:
    return personalize_insight(req.insight, req.profile, req.state)


@router.post("/personalize/compare", response_model=CompareResponse)
def personalize_compare(req: CompareRequest) -> CompareResponse:
    result = compare_fan_analyst(
        req.insight,
        state=req.state,
        fan=req.fan,
        analyst=req.analyst,
    )
    return CompareResponse(fan=result["fan"], analyst=result["analyst"])


@router.post(
    "/matches/{match_id}/personalize/{seq}/compare",
    response_model=CompareResponse,
)
def personalize_compare_at_seq(
    match_id: str,
    seq: int,
    seed: int = Query(42),
    favorite_club_id: str = Query("northbridge"),
    player_focus: str = Query("nb-9"),
) -> CompareResponse:
    from app.models.profile import default_analyst_profile, default_fan_profile

    events = resolve_events(match_id, seed=seed)
    try:
        insight = explain_event(events=events, seq=seq)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    engine = MatchStateEngine(match_id=match_id)
    state = engine.apply_all([e for e in events if e.seq <= seq])
    fan = default_fan_profile(
        favorite_club_id=favorite_club_id,
        favorite_player_id=player_focus,
        player_focus=player_focus,
    )
    analyst = default_analyst_profile()
    result = compare_fan_analyst(insight, state=state, fan=fan, analyst=analyst)
    return CompareResponse(fan=result["fan"], analyst=result["analyst"])
