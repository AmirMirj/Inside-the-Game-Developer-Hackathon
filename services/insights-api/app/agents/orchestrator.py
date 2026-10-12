"""
Pipeline orchestrator — agentic wiring for judges (Slice 7).

Order (matches ARCHITECTURE.md):
  Ingest events (given)
  → Interpret (MatchStateEngine)
  → MomentDetector + ExplainAgent
  → NarrativeAgent (beats)
  → PersonalizeAgent (Fan + Analyst)
  → Render payloads

This is a Semantic Kernel–style process loop implemented with explicit agents.
Swap ExplainAgent's LLM client to Azure OpenAI when credentials are set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.agents.explain_agent import ExplainAgent, get_explain_agent
from app.agents.narrative_agent import NarrativeAgent
from app.agents.personalize_agent import PersonalizeAgent
from app.config import get_settings
from app.models.events import MatchEvent
from app.models.insight import MatchInsight
from app.models.narrative import MatchRecap, StoryBeat
from app.models.profile import (
    ViewerProfile,
    default_analyst_profile,
    default_fan_profile,
)
from app.models.render import RenderPayload
from app.models.state import MatchState
from app.pipeline.interpret import MatchStateEngine
from app.pipeline.moments import MomentDetector
from app.pipeline.render import insight_to_render


@dataclass
class OrchestratorStep:
    name: str
    status: Literal["ok", "skipped"]
    detail: str


@dataclass
class PipelineResult:
    match_id: str
    final_state: MatchState
    insights: list[MatchInsight] = field(default_factory=list)
    story_beats: list[StoryBeat] = field(default_factory=list)
    renders: list[RenderPayload] = field(default_factory=list)
    personalized: dict[str, list[RenderPayload]] = field(default_factory=dict)
    recap_en: MatchRecap | None = None
    recap_es: MatchRecap | None = None
    steps: list[OrchestratorStep] = field(default_factory=list)
    explain_provider: str = "mock"
    synthetic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "synthetic": self.synthetic,
            "explain_provider": self.explain_provider,
            "steps": [
                {"name": s.name, "status": s.status, "detail": s.detail} for s in self.steps
            ],
            "final_state": self.final_state.model_dump(mode="json"),
            "insights": [i.model_dump(mode="json") for i in self.insights],
            "story_beats": [b.model_dump(mode="json") for b in self.story_beats],
            "renders": [r.model_dump(mode="json") for r in self.renders],
            "personalized": {
                role: [r.model_dump(mode="json") for r in payloads]
                for role, payloads in self.personalized.items()
            },
            "recap_en": self.recap_en.model_dump(mode="json") if self.recap_en else None,
            "recap_es": self.recap_es.model_dump(mode="json") if self.recap_es else None,
        }


class MatchIntelligenceOrchestrator:
    """
    Single entry that runs the multi-agent pipeline on an ordered event list.
    """

    def __init__(
        self,
        *,
        explain_agent: ExplainAgent | None = None,
        narrative_agent: NarrativeAgent | None = None,
        personalize_agent: PersonalizeAgent | None = None,
        fan_profile: ViewerProfile | None = None,
        analyst_profile: ViewerProfile | None = None,
    ) -> None:
        self.explain = explain_agent or get_explain_agent()
        self.narrative = narrative_agent or NarrativeAgent()
        self.personalize = personalize_agent or PersonalizeAgent()
        self.fan_profile = fan_profile or default_fan_profile()
        self.analyst_profile = analyst_profile or default_analyst_profile()
        self.detector = MomentDetector()

    def run(
        self,
        events: list[MatchEvent],
        *,
        min_priority: str = "medium",
        insight_limit: int = 12,
        include_recap: bool = True,
    ) -> PipelineResult:
        if not events:
            raise ValueError("orchestrator requires at least one event")

        match_id = events[0].match_id
        ordered = sorted(events, key=lambda e: e.seq)
        rank = {"low": 0, "medium": 1, "high": 2}
        min_rank = rank.get(min_priority, 1)

        steps: list[OrchestratorStep] = []
        engine = MatchStateEngine(match_id=match_id)
        recent: list[MatchEvent] = []
        insights: list[MatchInsight] = []
        renders: list[RenderPayload] = []
        fan_renders: list[RenderPayload] = []
        analyst_renders: list[RenderPayload] = []

        # --- Interpret + Explain loop ---
        for event in ordered:
            state = engine.apply(event)
            recent.append(event)
            moment = self.detector.evaluate(event, state)
            if moment is None:
                continue
            if rank.get(moment.priority, 0) < min_rank:
                continue
            if len(insights) >= insight_limit:
                break

            insight = self.explain.explain(
                moment=moment,
                event=event,
                state=state,
                recent_events=recent,
            )
            insights.append(insight)
            render = insight_to_render(insight)
            renders.append(render)
            fan_renders.append(
                self.personalize.personalize(
                    insight=insight,
                    profile=self.fan_profile,
                    state=state,
                )
            )
            analyst_renders.append(
                self.personalize.personalize(
                    insight=insight,
                    profile=self.analyst_profile,
                    state=state,
                )
            )

        final_state = engine.state
        steps.append(
            OrchestratorStep(
                "interpret",
                "ok",
                f"Aggregated {len(ordered)} events → clock {final_state.match_clock}",
            )
        )
        steps.append(
            OrchestratorStep(
                "explain",
                "ok",
                f"Produced {len(insights)} insights via {self.explain.client.provider_name}",
            )
        )

        # --- Narrative beats ---
        beats = self.narrative.beats_from_insights(insights, language="en")
        steps.append(
            OrchestratorStep("narrative", "ok", f"Emitted {len(beats)} story beats")
        )

        # --- Personalize summary step (already applied per insight) ---
        steps.append(
            OrchestratorStep(
                "personalize",
                "ok",
                f"Projected Fan ({len(fan_renders)}) and Analyst ({len(analyst_renders)}) variants",
            )
        )

        recap_en = None
        recap_es = None
        if include_recap and insights:
            multi = self.narrative.multilang_recap(
                match_id=match_id,
                insights=insights,
                state=final_state,
                languages=("en", "es"),
            )
            recap_en = multi.recaps["en"]
            recap_es = multi.recaps["es"]
            steps.append(
                OrchestratorStep(
                    "recap",
                    "ok",
                    f"EN ~{recap_en.estimated_read_seconds}s / ES ~{recap_es.estimated_read_seconds}s",
                )
            )
        else:
            steps.append(OrchestratorStep("recap", "skipped", "No insights or disabled"))

        provider = get_settings().resolve_explain_provider()
        return PipelineResult(
            match_id=match_id,
            final_state=final_state,
            insights=insights,
            story_beats=beats,
            renders=renders,
            personalized={"fan": fan_renders, "analyst": analyst_renders},
            recap_en=recap_en,
            recap_es=recap_es,
            steps=steps,
            explain_provider=provider if provider == "azure" else "mock",
            synthetic=True,
        )
