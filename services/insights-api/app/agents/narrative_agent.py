"""NarrativeAgent — story beats + multi-language match recaps."""

from __future__ import annotations

from uuid import uuid4

from app.models.insight import MatchInsight
from app.models.narrative import MatchRecap, MultiLangRecap, RecapMilestone, StoryBeat
from app.models.state import MatchState

SUPPORTED_LANGS = ("en", "es")

# Lightweight ES templates for demo/offline (Azure can refine later)
_ES = {
    "beat_goal": "Gol que cambia el relato",
    "beat_shot": "Ocasión clara",
    "beat_pressure": "Sube la presión",
    "beat_turnover": "Pérdida que abre el partido",
    "beat_tackle": "Entrada que recupera el control",
    "beat_default": "Momento clave",
    "recap_title": "Resumen automático del partido (sintético)",
    "intro": (
        "Este resumen usa solo datos sintéticos de fútbol. "
        "El marcador actual es {score}."
    ),
    "arc": (
        "El partido avanzó con un ritmo {tempo}. "
        "La presión media reciente fue {pressure:.2f} "
        "(variación {swing:+.2f})."
    ),
    "milestone": "En el minuto {clock}: {label}.",
    "players": "Jugadores mencionados en los momentos clave: {players}.",
    "close": (
        "En conjunto, estos hitos explican no solo qué ocurrió, "
        "sino por qué importó para el control del juego. "
        "Listo para estudio, streaming o personalización por aficionado."
    ),
}


class NarrativeAgent:
    """Build in-match beats and a 60–90s read recap in EN (+ ES)."""

    def beats_from_insights(
        self,
        insights: list[MatchInsight],
        *,
        language: str = "en",
        limit: int = 12,
    ) -> list[StoryBeat]:
        lang = language if language in SUPPORTED_LANGS else "en"
        beats: list[StoryBeat] = []
        for insight in insights[:limit]:
            title, text = self._beat_copy(insight, lang)
            beats.append(
                StoryBeat(
                    beat_id=uuid4(),
                    match_id=insight.match_id,
                    match_clock=insight.match_clock,
                    title=title,
                    text=text,
                    language=lang,
                    source_event_seq=insight.source_event_seq,
                    trigger=insight.trigger,
                    priority=insight.priority,
                    synthetic=True,
                )
            )
        return beats

    def recap(
        self,
        *,
        match_id: str,
        insights: list[MatchInsight],
        state: MatchState,
        language: str = "en",
    ) -> MatchRecap:
        lang = language if language in SUPPORTED_LANGS else "en"
        milestones = [
            RecapMilestone(
                match_clock=i.match_clock,
                label=i.headline,
                trigger=i.trigger,
            )
            for i in insights[:8]
        ]
        players = sorted(
            {
                (e.name or e.id)
                for i in insights
                for e in i.entities
                if e.kind == "player"
            }
        )
        score = dict(state.score)
        body = self._recap_body(
            lang=lang,
            score=score,
            state=state,
            milestones=milestones,
            players=players,
        )
        words = len(body.split())
        # ~150 wpm spoken/studio read
        read_s = max(60, min(90, int(round(words / 2.5))))
        title = (
            "Automated match recap (synthetic)"
            if lang == "en"
            else _ES["recap_title"]
        )
        return MatchRecap(
            recap_id=uuid4(),
            match_id=match_id,
            language=lang,
            title=title,
            body=body,
            word_count=words,
            estimated_read_seconds=read_s,
            milestones=milestones,
            player_mentions=players,
            score=score,
            provider="mock",
            synthetic=True,
        )

    def multilang_recap(
        self,
        *,
        match_id: str,
        insights: list[MatchInsight],
        state: MatchState,
        languages: tuple[str, ...] = SUPPORTED_LANGS,
    ) -> MultiLangRecap:
        recaps = {
            lang: self.recap(
                match_id=match_id,
                insights=insights,
                state=state,
                language=lang,
            )
            for lang in languages
        }
        return MultiLangRecap(
            match_id=match_id,
            languages=list(languages),
            recaps=recaps,
            synthetic=True,
        )

    def _beat_copy(self, insight: MatchInsight, lang: str) -> tuple[str, str]:
        trigger = insight.trigger or "moment"
        if lang == "es":
            titles = {
                "goal": _ES["beat_goal"],
                "shot": _ES["beat_shot"],
                "pressure_spike": _ES["beat_pressure"],
                "turnover": _ES["beat_turnover"],
                "tackle_won": _ES["beat_tackle"],
            }
            title = f"{titles.get(trigger, _ES['beat_default'])} · {insight.match_clock}"
            text = (
                f"{insight.headline}. {insight.why_it_matters} "
                f"(Prioridad {insight.priority}.)"
            )
            return title, text

        title = f"{insight.headline}"
        text = (
            f"Story beat @ {insight.match_clock}: {insight.body} "
            f"Why it matters: {insight.why_it_matters}"
        )
        return title, text

    def _recap_body(
        self,
        *,
        lang: str,
        score: dict[str, int],
        state: MatchState,
        milestones: list[RecapMilestone],
        players: list[str],
    ) -> str:
        score_txt = f"{score.get('home', 0)}-{score.get('away', 0)}"
        if lang == "es":
            parts = [
                _ES["intro"].format(score=score_txt),
                _ES["arc"].format(
                    tempo=state.rhythm.tempo,
                    pressure=state.pressure.recent_avg,
                    swing=state.pressure.swing,
                ),
            ]
            for m in milestones:
                parts.append(
                    _ES["milestone"].format(clock=m.match_clock, label=m.label)
                )
            if players:
                parts.append(_ES["players"].format(players=", ".join(players)))
            parts.append(_ES["close"])
            # Pad to studio read length with context lines
            parts.append(
                "La narración conecta posesión, presión y ocasiones para un relato "
                "claro en estudio o streaming, sin usar datos reales de la Premier League."
            )
            return " ".join(parts)

        parts = [
            f"This automated recap uses synthetic football data only. "
            f"The scoreline stands at {score_txt}.",
            f"Through the segment the tempo read {state.rhythm.tempo}, "
            f"with recent pressure averaging {state.pressure.recent_avg:.2f} "
            f"(swing {state.pressure.swing:+.2f}) and "
            f"{state.rhythm.events_per_minute:.1f} events per minute in the live window.",
        ]
        if milestones:
            parts.append("Key narrative milestones:")
            for m in milestones:
                trig = f" [{m.trigger}]" if m.trigger else ""
                parts.append(f"At {m.match_clock}{trig}: {m.label}.")
        if players:
            parts.append(
                "Player context across those moments includes "
                + ", ".join(players)
                + "."
            )
        home = state.home_team_id or "home"
        away = state.away_team_id or "away"
        home_stats = state.teams.get(home)
        away_stats = state.teams.get(away)
        if home_stats and away_stats:
            parts.append(
                f"Team shape: {home} possession {home_stats.possession_pct}% "
                f"with {home_stats.shots} shots; {away} possession "
                f"{away_stats.possession_pct}% with {away_stats.shots} shots."
            )
        parts.append(
            "Taken together, these beats explain not only what happened, "
            "but why control, chance quality, and momentum shifted — "
            "ready for studio lower-thirds, streaming recaps, or fan personalization. "
            "No real Premier League match data is used in this narrative."
        )
        return " ".join(parts)
