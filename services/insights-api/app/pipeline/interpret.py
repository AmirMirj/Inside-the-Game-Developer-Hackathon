"""Stage B — Interpret events into live match statistics and state."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from app.models.events import EventType, MatchEvent
from app.models.state import (
    MatchState,
    PassQuality,
    PressureState,
    RhythmState,
    TeamStats,
)

WINDOW_SECONDS = 300  # 5 match-clock minutes


def clock_to_seconds(match_clock: str) -> int:
    minutes, seconds = match_clock.split(":")
    return int(minutes) * 60 + int(seconds)


@dataclass
class _PassAccum:
    count: int = 0
    distance_sum: float = 0.0
    difficulty_sum: float = 0.0


@dataclass
class MatchStateEngine:
    """Deterministic aggregator: apply events in order to build MatchState."""

    match_id: str
    home_team_id: str | None = None
    away_team_id: str | None = None
    _state: MatchState = field(init=False)
    _prev_clock_sec: int | None = field(default=None, init=False)
    _pressure_samples: deque[tuple[int, float]] = field(default_factory=deque, init=False)
    _prev_pressure_avg: float = field(default=0.0, init=False)
    _event_times: deque[int] = field(default_factory=deque, init=False)
    _pass_accum: dict[str, _PassAccum] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._state = MatchState(
            match_id=self.match_id,
            home_team_id=self.home_team_id,
            away_team_id=self.away_team_id,
        )

    @property
    def state(self) -> MatchState:
        return self._state.model_copy(deep=True)

    def _ensure_team(self, team_id: str) -> TeamStats:
        if team_id not in self._state.teams:
            self._state.teams[team_id] = TeamStats(team_id=team_id)
        return self._state.teams[team_id]

    def _credit_possession_time(self, clock_sec: int) -> None:
        if self._prev_clock_sec is None or self._state.possessing_team_id is None:
            return
        delta = max(0, clock_sec - self._prev_clock_sec)
        if delta == 0:
            return
        team = self._ensure_team(self._state.possessing_team_id)
        team.possession_seconds += float(delta)

    def _recompute_possession_pct(self) -> None:
        total = sum(t.possession_seconds for t in self._state.teams.values())
        if total <= 0:
            for team in self._state.teams.values():
                team.possession_pct = 0.0
            return
        for team in self._state.teams.values():
            team.possession_pct = round(100.0 * team.possession_seconds / total, 1)

    def _update_pressure(self, clock_sec: int, intensity: float | None = None) -> None:
        if intensity is not None:
            self._pressure_samples.append((clock_sec, intensity))
        cutoff = clock_sec - WINDOW_SECONDS
        while self._pressure_samples and self._pressure_samples[0][0] < cutoff:
            self._pressure_samples.popleft()

        if not self._pressure_samples:
            current = 0.0
            recent_avg = 0.0
        else:
            values = [v for _, v in self._pressure_samples]
            current = values[-1]
            recent_avg = sum(values) / len(values)

        swing = round(recent_avg - self._prev_pressure_avg, 3)
        self._prev_pressure_avg = recent_avg
        self._state.pressure = PressureState(
            current=round(current, 3),
            recent_avg=round(recent_avg, 3),
            swing=swing,
            window_seconds=WINDOW_SECONDS,
            sample_count=len(self._pressure_samples),
        )

    def _update_rhythm(self, clock_sec: int) -> None:
        self._event_times.append(clock_sec)
        cutoff = clock_sec - WINDOW_SECONDS
        while self._event_times and self._event_times[0] < cutoff:
            self._event_times.popleft()

        count = len(self._event_times)
        minutes = WINDOW_SECONDS / 60.0
        epm = round(count / minutes, 2)
        if epm < 2.0:
            tempo: str = "slow"
        elif epm < 5.0:
            tempo = "medium"
        else:
            tempo = "high"
        self._state.rhythm = RhythmState(
            events_per_minute=epm,
            tempo=tempo,  # type: ignore[arg-type]
            window_seconds=WINDOW_SECONDS,
            event_count=count,
        )

    def _apply_pass(self, event: MatchEvent) -> None:
        if not event.team_id:
            return
        team = self._ensure_team(event.team_id)
        team.passes_attempted += 1
        accurate = bool(event.payload.get("accurate", False))
        if accurate:
            team.passes_accurate += 1
        team.pass_accuracy = (
            round(100.0 * team.passes_accurate / team.passes_attempted, 1)
            if team.passes_attempted
            else 0.0
        )

        distance = event.payload.get("distance_m")
        difficulty = event.payload.get("difficulty")
        accum = self._pass_accum.setdefault(event.team_id, _PassAccum())
        accum.count += 1
        if isinstance(distance, (int, float)):
            accum.distance_sum += float(distance)
            team.avg_pass_distance_m = round(accum.distance_sum / accum.count, 2)
        if isinstance(difficulty, (int, float)):
            accum.difficulty_sum += float(difficulty)
            team.avg_pass_difficulty = round(accum.difficulty_sum / accum.count, 3)

        self._state.last_pass_quality = PassQuality(
            distance_m=float(distance) if isinstance(distance, (int, float)) else None,
            accurate=accurate,
            difficulty=float(difficulty) if isinstance(difficulty, (int, float)) else None,
            player_id=event.player_id,
            team_id=event.team_id,
            event_id=str(event.event_id),
            match_clock=event.match_clock,
        )

    def apply(self, event: MatchEvent) -> MatchState:
        if event.match_id != self.match_id:
            raise ValueError(
                f"event match_id {event.match_id!r} does not match engine {self.match_id!r}"
            )

        clock_sec = clock_to_seconds(event.match_clock)
        self._credit_possession_time(clock_sec)

        self._state.match_clock = event.match_clock
        self._state.period = event.period
        self._state.last_seq = event.seq

        if event.type == EventType.metadata:
            payload = event.payload
            if payload.get("kickoff"):
                self._state.home_team_id = payload.get("home_team_id") or self.home_team_id
                self._state.away_team_id = payload.get("away_team_id") or self.away_team_id
                if self._state.home_team_id:
                    self._ensure_team(self._state.home_team_id)
                    self._state.possessing_team_id = self._state.home_team_id
                if self._state.away_team_id:
                    self._ensure_team(self._state.away_team_id)
            if "score" in payload and isinstance(payload["score"], dict):
                self._state.score = {
                    "home": int(payload["score"].get("home", 0)),
                    "away": int(payload["score"].get("away", 0)),
                }

        elif event.type == EventType.pass_:
            self._apply_pass(event)

        elif event.type == EventType.shot:
            if event.team_id:
                team = self._ensure_team(event.team_id)
                team.shots += 1
                if event.payload.get("on_target"):
                    team.shots_on_target += 1

        elif event.type == EventType.tackle:
            if event.team_id:
                team = self._ensure_team(event.team_id)
                team.tackles += 1
                if event.payload.get("won"):
                    team.tackles_won += 1
                    self._state.possessing_team_id = event.team_id

        elif event.type == EventType.possession_change:
            if event.team_id:
                self._ensure_team(event.team_id)
                self._state.possessing_team_id = event.team_id

        elif event.type == EventType.pressure:
            intensity = event.payload.get("intensity")
            self._update_pressure(
                clock_sec,
                float(intensity) if isinstance(intensity, (int, float)) else None,
            )

        elif event.type == EventType.goal:
            if event.team_id:
                team = self._ensure_team(event.team_id)
                team.goals += 1
            score_after = event.payload.get("score_after")
            if isinstance(score_after, dict):
                self._state.score = {
                    "home": int(score_after.get("home", self._state.score["home"])),
                    "away": int(score_after.get("away", self._state.score["away"])),
                }
            # Kickoff restart: concede possession to conceding team if known
            if event.team_id and self._state.home_team_id and self._state.away_team_id:
                self._state.possessing_team_id = (
                    self._state.away_team_id
                    if event.team_id == self._state.home_team_id
                    else self._state.home_team_id
                )

        if event.type != EventType.pressure:
            # Still refresh pressure window decay on clock advance
            self._update_pressure(clock_sec, intensity=None)

        self._update_rhythm(clock_sec)
        self._recompute_possession_pct()
        self._prev_clock_sec = clock_sec
        return self.state

    def apply_all(self, events: list[MatchEvent]) -> MatchState:
        ordered = sorted(events, key=lambda e: (e.seq, clock_to_seconds(e.match_clock)))
        for event in ordered:
            self.apply(event)
        return self.state


def build_state(match_id: str, events: list[MatchEvent]) -> MatchState:
    engine = MatchStateEngine(match_id=match_id)
    return engine.apply_all(events)
