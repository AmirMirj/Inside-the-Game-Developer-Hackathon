"""Stage E — personalize insights into role-specific render payloads."""

from __future__ import annotations

from app.agents.personalize_agent import PersonalizeAgent
from app.models.insight import MatchInsight
from app.models.profile import (
    ViewerProfile,
    default_analyst_profile,
    default_fan_profile,
    default_studio_profile,
)
from app.models.render import RenderPayload
from app.models.state import MatchState
from app.pipeline.explain import explain_event
from app.pipeline.interpret import MatchStateEngine

_agent = PersonalizeAgent()


def personalize_insight(
    insight: MatchInsight,
    profile: ViewerProfile,
    state: MatchState | None = None,
) -> RenderPayload:
    return _agent.personalize(insight=insight, profile=profile, state=state)


def compare_fan_analyst(
    insight: MatchInsight,
    *,
    state: MatchState | None = None,
    fan: ViewerProfile | None = None,
    analyst: ViewerProfile | None = None,
) -> dict[str, RenderPayload]:
    return _agent.compare(
        insight=insight,
        fan=fan or default_fan_profile(),
        analyst=analyst or default_analyst_profile(),
        state=state,
    )


def personalize_at_seq(
    events: list,
    seq: int,
    profile: ViewerProfile,
) -> tuple[MatchInsight, MatchState, RenderPayload]:
    insight = explain_event(events=events, seq=seq)
    engine = MatchStateEngine(match_id=events[0].match_id)
    state = engine.apply_all([e for e in events if e.seq <= seq])
    render = personalize_insight(insight, profile, state)
    return insight, state, render


def default_profiles() -> dict[str, ViewerProfile]:
    return {
        "fan": default_fan_profile(),
        "analyst": default_analyst_profile(),
        "studio": default_studio_profile(),
    }
