"""Stage D — shape insights into timed studio / overlay payloads."""

from __future__ import annotations

from uuid import uuid4

from app.models.insight import MatchInsight
from app.models.render import RenderPayload, RenderText


def insight_to_render(insight: MatchInsight) -> RenderPayload:
    """Map a Stage C insight into the Stage D render contract."""
    return RenderPayload(
        render_id=uuid4(),
        insight_id=str(insight.insight_id),
        match_id=insight.match_id,
        match_clock=insight.match_clock,
        duration_ms=insight.duration_ms,
        priority=insight.priority,
        overlay_type=insight.overlay_type,
        text=RenderText(
            headline=insight.headline,
            body=insight.body,
            why_it_matters=insight.why_it_matters,
        ),
        entities=list(insight.entities),
        source_event_seq=insight.source_event_seq,
        trigger=insight.trigger,
        confidence=insight.confidence,
        synthetic=True,
    )


def insights_to_timeline(insights: list[MatchInsight]) -> list[RenderPayload]:
    """Ordered render timeline for demo replay (by match clock / seq)."""

    def sort_key(insight: MatchInsight) -> tuple[int, int]:
        parts = insight.match_clock.split(":")
        clock = int(parts[0]) * 60 + int(parts[1])
        return (clock, insight.source_event_seq or 0)

    ordered = sorted(insights, key=sort_key)
    return [insight_to_render(i) for i in ordered]
