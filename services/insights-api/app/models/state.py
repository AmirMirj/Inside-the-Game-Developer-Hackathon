"""Live match state models (Stage B — Interpret)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PassQuality(BaseModel):
    distance_m: float | None = None
    accurate: bool | None = None
    difficulty: float | None = None
    player_id: str | None = None
    team_id: str | None = None
    event_id: str | None = None
    match_clock: str | None = None


class TeamStats(BaseModel):
    team_id: str
    passes_attempted: int = 0
    passes_accurate: int = 0
    pass_accuracy: float = 0.0
    avg_pass_distance_m: float | None = None
    avg_pass_difficulty: float | None = None
    shots: int = 0
    shots_on_target: int = 0
    tackles: int = 0
    tackles_won: int = 0
    goals: int = 0
    possession_seconds: float = 0.0
    possession_pct: float = 0.0


class PressureState(BaseModel):
    """Pressure from a recent match-clock window."""

    current: float = 0.0
    recent_avg: float = 0.0
    swing: float = 0.0
    window_seconds: int = 300
    sample_count: int = 0


class RhythmState(BaseModel):
    """Game rhythm from recent event density."""

    events_per_minute: float = 0.0
    tempo: Literal["slow", "medium", "high"] = "slow"
    window_seconds: int = 300
    event_count: int = 0


class MatchState(BaseModel):
    match_id: str
    match_clock: str = "0:00"
    period: int = 1
    last_seq: int = -1
    score: dict[str, int] = Field(default_factory=lambda: {"home": 0, "away": 0})
    home_team_id: str | None = None
    away_team_id: str | None = None
    possessing_team_id: str | None = None
    teams: dict[str, TeamStats] = Field(default_factory=dict)
    pressure: PressureState = Field(default_factory=PressureState)
    rhythm: RhythmState = Field(default_factory=RhythmState)
    last_pass_quality: PassQuality | None = None
    synthetic: bool = True
