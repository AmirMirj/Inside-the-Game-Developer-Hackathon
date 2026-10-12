"""Slice 6 — story beats and multi-language recaps from explained moments."""

from __future__ import annotations

from app.agents.explain_agent import ExplainAgent
from app.agents.llm import MockLlmClient
from app.agents.narrative_agent import NarrativeAgent
from app.models.insight import MatchInsight
from app.models.narrative import MatchRecap, MultiLangRecap, StoryBeat
from app.models.state import MatchState
from app.pipeline.explain import scan_insights
from app.pipeline.interpret import MatchStateEngine


def _insights_and_state(
    events: list,
    *,
    min_priority: str = "medium",
    limit: int = 12,
) -> tuple[list[MatchInsight], MatchState]:
    if not events:
        raise ValueError("no events")
    match_id = events[0].match_id
    agent = ExplainAgent(client=MockLlmClient())
    insights = scan_insights(
        events,
        agent=agent,
        min_priority=min_priority,
        limit=limit,
    )
    state = MatchStateEngine(match_id=match_id).apply_all(events)
    return insights, state


def build_beats(
    events: list,
    *,
    language: str = "en",
    min_priority: str = "medium",
    limit: int = 12,
) -> list[StoryBeat]:
    insights, _ = _insights_and_state(
        events, min_priority=min_priority, limit=limit
    )
    return NarrativeAgent().beats_from_insights(
        insights, language=language, limit=limit
    )


def build_recap(
    events: list,
    *,
    language: str = "en",
    min_priority: str = "medium",
    limit: int = 12,
) -> MatchRecap:
    insights, state = _insights_and_state(
        events, min_priority=min_priority, limit=limit
    )
    return NarrativeAgent().recap(
        match_id=events[0].match_id,
        insights=insights,
        state=state,
        language=language,
    )


def build_multilang_recap(
    events: list,
    *,
    languages: tuple[str, ...] = ("en", "es"),
    min_priority: str = "medium",
    limit: int = 12,
) -> MultiLangRecap:
    insights, state = _insights_and_state(
        events, min_priority=min_priority, limit=limit
    )
    return NarrativeAgent().multilang_recap(
        match_id=events[0].match_id,
        insights=insights,
        state=state,
        languages=languages,
    )
