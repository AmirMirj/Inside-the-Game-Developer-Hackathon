"""Rule-based key-moment detector (Stage C)."""

from __future__ import annotations

from app.models.events import EventType, MatchEvent
from app.models.insight import CandidateMoment
from app.models.state import MatchState


class MomentDetector:
    """Flag candidate moments from event + live state (no LLM)."""

    def __init__(self, *, pressure_intensity_min: float = 0.75, pressure_swing_min: float = 0.15):
        self.pressure_intensity_min = pressure_intensity_min
        self.pressure_swing_min = pressure_swing_min
        self._prev_event: MatchEvent | None = None

    def evaluate(self, event: MatchEvent, state: MatchState) -> CandidateMoment | None:
        candidate = self._evaluate(event, state)
        self._prev_event = event
        return candidate

    def _evaluate(self, event: MatchEvent, state: MatchState) -> CandidateMoment | None:
        if event.type == EventType.goal:
            return self._moment(
                event,
                trigger="goal",
                priority="high",
                reason="Goal changes the scoreline and match narrative.",
            )

        if event.type == EventType.shot:
            xg = event.payload.get("xg")
            on_target = bool(event.payload.get("on_target"))
            priority = "high" if (on_target or (isinstance(xg, (int, float)) and xg >= 0.2)) else "medium"
            return self._moment(
                event,
                trigger="shot",
                priority=priority,
                reason="Shot attempt under current score and pressure context.",
            )

        if event.type == EventType.pressure:
            intensity = event.payload.get("intensity")
            intense = isinstance(intensity, (int, float)) and intensity >= self.pressure_intensity_min
            swing = abs(state.pressure.swing) >= self.pressure_swing_min
            if intense or swing:
                return self._moment(
                    event,
                    trigger="pressure_spike",
                    priority="medium" if not intense else "high",
                    reason="Pressure intensity or swing signals control vs chaos shift.",
                )

        if event.type == EventType.possession_change:
            prev = self._prev_event
            after_pressure = prev is not None and prev.type == EventType.pressure
            zone = str(event.payload.get("reason", ""))
            if after_pressure or "tackle" in zone or "interception" in zone:
                return self._moment(
                    event,
                    trigger="turnover",
                    priority="medium",
                    reason="Turnover changes who controls the next phase.",
                )

        if event.type == EventType.tackle and event.payload.get("won"):
            return self._moment(
                event,
                trigger="tackle_won",
                priority="medium",
                reason="Won tackle can flip momentum and possession.",
            )

        return None

    @staticmethod
    def _moment(
        event: MatchEvent,
        *,
        trigger: str,
        priority: str,
        reason: str,
    ) -> CandidateMoment:
        return CandidateMoment(
            match_id=event.match_id,
            match_clock=event.match_clock,
            event_seq=event.seq,
            event_id=str(event.event_id),
            trigger=trigger,
            priority=priority,  # type: ignore[arg-type]
            reason=reason,
            event_type=event.type.value,
        )
