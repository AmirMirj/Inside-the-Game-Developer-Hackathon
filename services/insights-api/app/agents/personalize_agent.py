"""PersonalizeAgent — rewrite insight copy for fan / analyst / studio."""

from __future__ import annotations

from uuid import uuid4

from app.models.insight import MatchInsight
from app.models.profile import ViewerProfile
from app.models.render import RenderPayload, RenderText
from app.models.state import MatchState
from app.pipeline.render import insight_to_render


class PersonalizeAgent:
    """
    Deterministic personalization transform.

    Changes substance (headline/body/why), not only styling.
    Optional Azure rewrite can wrap this later; mock path stays reliable for demos.
    """

    def personalize(
        self,
        *,
        insight: MatchInsight,
        profile: ViewerProfile,
        state: MatchState | None = None,
    ) -> RenderPayload:
        base = insight_to_render(insight)
        headline, body, why = self._rewrite(insight, profile, state)

        return RenderPayload(
            render_id=uuid4(),
            insight_id=base.insight_id,
            match_id=base.match_id,
            match_clock=base.match_clock,
            duration_ms=base.duration_ms
            if profile.role != "studio"
            else min(base.duration_ms, 6000),
            priority=base.priority,
            overlay_type=base.overlay_type
            if profile.role != "studio"
            else "lower_third",
            text=RenderText(headline=headline, body=body, why_it_matters=why),
            entities=list(base.entities),
            source_event_seq=base.source_event_seq,
            trigger=base.trigger,
            confidence=base.confidence,
            synthetic=True,
        )

    def compare(
        self,
        *,
        insight: MatchInsight,
        fan: ViewerProfile,
        analyst: ViewerProfile,
        state: MatchState | None = None,
    ) -> dict[str, RenderPayload]:
        return {
            "fan": self.personalize(insight=insight, profile=fan, state=state),
            "analyst": self.personalize(insight=insight, profile=analyst, state=state),
        }

    def _rewrite(
        self,
        insight: MatchInsight,
        profile: ViewerProfile,
        state: MatchState | None,
    ) -> tuple[str, str, str]:
        score = state.score if state else {"home": "?", "away": "?"}
        score_txt = f"{score.get('home', '?')}-{score.get('away', '?')}"
        trigger = (insight.trigger or "moment").replace("_", " ")
        focus = profile.modes.player_focus
        focus_name = self._entity_name(insight, focus) if focus else None
        club_bias = self._club_bias_phrase(insight, profile)
        player_bias = self._player_focus_phrase(insight, profile, focus_name)

        if profile.role == "fan":
            headline = self._fan_headline(insight, focus_name, club_bias)
            body = (
                f"{player_bias}{club_bias}"
                f"At {insight.match_clock}, this {trigger} lights up the story. "
                f"{self._plain(insight.body)}"
            ).strip()
            why = (
                f"Scoreline {score_txt}. "
                f"For a fan, this matters because it changes how the next few minutes feel"
                f"{' for your player' if focus_name else ''}"
                f"{' and your club' if club_bias else ''}. "
                f"{self._plain(insight.why_it_matters)}"
            )
            return headline, body, why

        if profile.role == "analyst":
            metrics = self._analyst_metrics(state, profile)
            headline = f"{trigger.title()} · state read @ {insight.match_clock}"
            body = (
                f"{metrics}"
                f"Signal: {insight.trigger or 'event'} (priority {insight.priority}, "
                f"confidence {insight.confidence:.2f}). "
                f"Base note: {self._plain(insight.body)}"
            )
            why = (
                f"Score {score_txt}. "
                f"Analytical lens: pressure/rhythm/possession context explains leverage, "
                f"not just the discrete event. {self._plain(insight.why_it_matters)}"
            )
            return headline, body, why

        # studio — tight on-screen copy
        headline = f"{trigger.title()} · {insight.match_clock}"
        body = self._plain(insight.headline)
        why = f"{score_txt}. {self._plain(insight.why_it_matters)[:160]}"
        return headline, body, why

    @staticmethod
    def _plain(text: str) -> str:
        return " ".join((text or "").split())

    @staticmethod
    def _entity_name(insight: MatchInsight, player_id: str | None) -> str | None:
        if not player_id:
            return None
        for ent in insight.entities:
            if ent.id == player_id and ent.name:
                return ent.name
        return player_id

    def _club_bias_phrase(self, insight: MatchInsight, profile: ViewerProfile) -> str:
        if not profile.favorite_club_ids:
            return ""
        involved = any(
            e.kind in {"team", "club"} and e.id in profile.favorite_club_ids
            for e in insight.entities
        )
        # also check evidence labels loosely via team ids on insight — entities preferred
        club = profile.favorite_club_ids[0]
        if involved:
            return f"Your club ({club}) is in the middle of this. "
        return f"Watching as a {club} supporter: "

    def _player_focus_phrase(
        self,
        insight: MatchInsight,
        profile: ViewerProfile,
        focus_name: str | None,
    ) -> str:
        focus = profile.modes.player_focus or (
            profile.favorite_player_ids[0] if profile.favorite_player_ids else None
        )
        if not focus:
            return ""
        involved = any(e.id == focus for e in insight.entities)
        name = focus_name or focus
        if involved:
            return f"Player focus — {name} is directly involved. "
        return f"Player focus on {name} (not on this action, still framing the story). "

    def _fan_headline(
        self,
        insight: MatchInsight,
        focus_name: str | None,
        club_bias: str,
    ) -> str:
        if focus_name and any(
            e.id == (insight.entities[0].id if insight.entities else None)
            or (e.name == focus_name)
            for e in insight.entities
        ):
            return f"{focus_name} in the spotlight @ {insight.match_clock}"
        if club_bias:
            return f"Big moment for your side @ {insight.match_clock}"
        return f"Here's the story @ {insight.match_clock}"

    def _analyst_metrics(self, state: MatchState | None, profile: ViewerProfile) -> str:
        if state is None:
            return "No live state attached — qualitative read only. "
        metric = profile.modes.metric_focus or "pressure"
        bits = [
            f"possession {state.possessing_team_id or 'n/a'}",
            f"pressure {state.pressure.current:.2f} (avg {state.pressure.recent_avg:.2f}, swing {state.pressure.swing:+.2f})",
            f"rhythm {state.rhythm.tempo} ({state.rhythm.events_per_minute}/min)",
        ]
        if state.last_pass_quality:
            pq = state.last_pass_quality
            bits.append(
                f"last pass dist {pq.distance_m}m diff {pq.difficulty} acc {pq.accurate}"
            )
        focus_line = f"Metric focus: {metric}. "
        return focus_line + " | ".join(bits) + ". "
