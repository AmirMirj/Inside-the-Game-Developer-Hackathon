"""In-match story beats and automated match recaps (Slice 6)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class StoryBeat(BaseModel):
    beat_id: UUID
    match_id: str
    match_clock: str
    title: str
    text: str
    language: str = "en"
    source_event_seq: int | None = None
    trigger: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    synthetic: bool = True


class RecapMilestone(BaseModel):
    match_clock: str
    label: str
    trigger: str | None = None


class MatchRecap(BaseModel):
    recap_id: UUID
    match_id: str
    language: str
    title: str
    body: str
    word_count: int = Field(ge=0)
    estimated_read_seconds: int = Field(ge=0)
    milestones: list[RecapMilestone] = Field(default_factory=list)
    player_mentions: list[str] = Field(default_factory=list)
    score: dict[str, int] = Field(default_factory=dict)
    provider: Literal["mock", "azure_openai"] = "mock"
    synthetic: bool = True


class MultiLangRecap(BaseModel):
    match_id: str
    languages: list[str]
    recaps: dict[str, MatchRecap]
    synthetic: bool = True
