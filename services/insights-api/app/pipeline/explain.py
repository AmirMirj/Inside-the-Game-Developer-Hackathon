"""Stage C — detect key moments and explain why they matter."""

from __future__ import annotations

from app.agents.explain_agent import ExplainAgent, get_explain_agent
from app.models.events import MatchEvent
from app.models.insight import CandidateMoment, MatchInsight
from app.models.state import MatchState
from app.pipeline.interpret import MatchStateEngine
from app.pipeline.moments import MomentDetector


def detect_moments(events: list[MatchEvent]) -> list[tuple[CandidateMoment, MatchEvent, MatchState]]:
    """Run detector across an ordered event list; return candidates with state snapshots."""
    if not events:
        return []
    match_id = events[0].match_id
    engine = MatchStateEngine(match_id=match_id)
    detector = MomentDetector()
    found: list[tuple[CandidateMoment, MatchEvent, MatchState]] = []
    for event in sorted(events, key=lambda e: e.seq):
        state = engine.apply(event)
        moment = detector.evaluate(event, state)
        if moment is not None:
            found.append((moment, event, state))
    return found


def explain_event(
    *,
    events: list[MatchEvent],
    seq: int,
    agent: ExplainAgent | None = None,
) -> MatchInsight:
    """Rebuild state up to seq, detect, and explain. Raises ValueError if not a moment."""
    ordered = sorted(events, key=lambda e: e.seq)
    if not ordered:
        raise ValueError("no events")
    match_id = ordered[0].match_id
    engine = MatchStateEngine(match_id=match_id)
    detector = MomentDetector()
    explain = agent or get_explain_agent()
    recent: list[MatchEvent] = []
    target: MatchEvent | None = None
    target_moment: CandidateMoment | None = None
    target_state: MatchState | None = None

    for event in ordered:
        state = engine.apply(event)
        recent.append(event)
        moment = detector.evaluate(event, state)
        if event.seq == seq:
            target = event
            target_moment = moment
            target_state = state
            break

    if target is None or target_state is None:
        raise ValueError(f"event seq {seq} not found")
    if target_moment is None:
        raise ValueError(f"event seq {seq} is not a key moment")

    return explain.explain(
        moment=target_moment,
        event=target,
        state=target_state,
        recent_events=recent,
    )


def scan_insights(
    events: list[MatchEvent],
    *,
    agent: ExplainAgent | None = None,
    min_priority: str = "medium",
    limit: int | None = None,
) -> list[MatchInsight]:
    """Explain detected moments (optionally filtered by priority)."""
    rank = {"low": 0, "medium": 1, "high": 2}
    min_rank = rank.get(min_priority, 1)
    explain = agent or get_explain_agent()
    insights: list[MatchInsight] = []
    recent: list[MatchEvent] = []
    match_id = events[0].match_id if events else ""
    engine = MatchStateEngine(match_id=match_id)
    detector = MomentDetector()

    for event in sorted(events, key=lambda e: e.seq):
        state = engine.apply(event)
        recent.append(event)
        moment = detector.evaluate(event, state)
        if moment is None:
            continue
        if rank.get(moment.priority, 0) < min_rank:
            continue
        insights.append(
            explain.explain(
                moment=moment,
                event=event,
                state=state,
                recent_events=recent,
            )
        )
        if limit is not None and len(insights) >= limit:
            break
    return insights
