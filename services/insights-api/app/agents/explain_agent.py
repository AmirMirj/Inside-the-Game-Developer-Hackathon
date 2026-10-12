"""ExplainAgent — why a moment matters, grounded in match state."""

from __future__ import annotations

import json
from functools import lru_cache
from uuid import uuid4

from app.agents.llm import LlmClient, build_llm_client
from app.config import Settings, get_settings
from app.models.events import MatchEvent
from app.models.insight import (
    CandidateMoment,
    InsightEntity,
    InsightEvidence,
    MatchInsight,
)
from app.models.state import MatchState

SYSTEM_PROMPT = """You are a Premier League studio analyst for SYNTHETIC match data only.
Explain why a football moment matters using the provided live match STATE and EVENT.
Do not invent players or scores absent from the JSON.
Return a JSON object with keys:
headline (string), body (string), why_it_matters (string),
confidence (0-1 number), overlay_type (moment_card|lower_third|ticker),
duration_ms (integer milliseconds).
why_it_matters must reference score and at least one of pressure/rhythm/possession.
Keep language clear for broadcast. No markdown."""


class ExplainAgent:
    def __init__(self, client: LlmClient | None = None, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = client or build_llm_client(self.settings)

    def explain(
        self,
        *,
        moment: CandidateMoment,
        event: MatchEvent,
        state: MatchState,
        recent_events: list[MatchEvent] | None = None,
    ) -> MatchInsight:
        recent = recent_events or []
        user_payload = {
            "moment": moment.model_dump(mode="json"),
            "event": event.model_dump(mode="json"),
            "state": {
                "score": state.score,
                "match_clock": state.match_clock,
                "possessing_team_id": state.possessing_team_id,
                "pressure": state.pressure.model_dump(),
                "rhythm": state.rhythm.model_dump(),
                "teams": {
                    tid: {
                        "possession_pct": t.possession_pct,
                        "shots": t.shots,
                        "passes_attempted": t.passes_attempted,
                        "pass_accuracy": t.pass_accuracy,
                        "goals": t.goals,
                    }
                    for tid, t in state.teams.items()
                },
            },
            "recent_event_types": [e.type.value for e in recent[-5:]],
        }
        raw = self.client.complete_json(
            system=SYSTEM_PROMPT,
            user=json.dumps(user_payload),
        )

        evidence = [
            InsightEvidence(
                event_id=str(event.event_id),
                label=f"{event.type.value} @ {event.match_clock}",
            )
        ]
        for prev in recent[-3:]:
            if str(prev.event_id) == str(event.event_id):
                continue
            evidence.append(
                InsightEvidence(
                    event_id=str(prev.event_id),
                    label=f"{prev.type.value} @ {prev.match_clock}",
                )
            )

        entities: list[InsightEntity] = []
        if event.team_id:
            entities.append(InsightEntity(kind="team", id=event.team_id, name=event.team_id))
        if event.player_id:
            name = None
            for actor in event.actors:
                if actor.player_id == event.player_id:
                    name = actor.name
                    break
            entities.append(
                InsightEntity(kind="player", id=event.player_id, name=name)
            )

        provider = "azure_openai" if self.client.provider_name == "azure_openai" else "mock"
        priority = moment.priority
        overlay = raw.get("overlay_type") or "moment_card"
        if overlay not in {"lower_third", "moment_card", "recap_block", "ticker"}:
            overlay = "moment_card"
        try:
            confidence = float(raw.get("confidence") or 0.7)
        except (TypeError, ValueError):
            confidence = 0.7
        confidence = min(1.0, max(0.0, confidence))
        try:
            duration_ms = int(raw.get("duration_ms") or (10000 if priority == "high" else 8000))
        except (TypeError, ValueError):
            duration_ms = 8000

        return MatchInsight(
            insight_id=uuid4(),
            match_id=moment.match_id,
            match_clock=moment.match_clock,
            duration_ms=duration_ms,
            priority=priority,
            overlay_type=overlay,  # type: ignore[arg-type]
            headline=str(raw.get("headline") or f"Moment at {moment.match_clock}"),
            body=str(raw.get("body") or moment.reason),
            why_it_matters=str(
                raw.get("why_it_matters")
                or f"Score {state.score['home']}-{state.score['away']}; context from live state."
            ),
            evidence=evidence,
            entities=entities,
            confidence=confidence,
            trigger=moment.trigger,
            source_event_seq=moment.event_seq,
            provider=provider,  # type: ignore[arg-type]
            synthetic=True,
        )


@lru_cache
def get_explain_agent() -> ExplainAgent:
    return ExplainAgent()
