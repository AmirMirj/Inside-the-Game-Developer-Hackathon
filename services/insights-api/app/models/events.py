"""Pydantic models aligned with packages/schemas/match_event.schema.json."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class EventType(str, Enum):
    pass_ = "pass"
    shot = "shot"
    tackle = "tackle"
    possession_change = "possession_change"
    pressure = "pressure"
    metadata = "metadata"
    foul = "foul"
    card = "card"
    substitution = "substitution"
    goal = "goal"


class EventActor(BaseModel):
    """Player or team participant on an event."""

    role: str
    player_id: str | None = None
    team_id: str | None = None
    name: str | None = None


class MatchEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID
    match_id: str
    seq: int = Field(ge=0)
    match_clock: str
    period: int = Field(ge=1, le=2)
    type: EventType
    team_id: str | None = None
    player_id: str | None = None
    actors: list[EventActor] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    ts: datetime
    synthetic: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def timestamp(self) -> datetime:
        """Alias required by Slice 1 acceptance language."""
        return self.ts
