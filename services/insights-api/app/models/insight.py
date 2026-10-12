"""Structured match insights (Stage C — Explain)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class InsightEvidence(BaseModel):
    event_id: str
    label: str


class InsightEntity(BaseModel):
    kind: Literal["player", "club", "team"]
    id: str
    name: str | None = None


class MatchInsight(BaseModel):
    insight_id: UUID
    match_id: str
    match_clock: str
    duration_ms: int = 8000
    priority: Literal["low", "medium", "high"]
    overlay_type: Literal["lower_third", "moment_card", "recap_block", "ticker"] = (
        "moment_card"
    )
    headline: str
    body: str
    why_it_matters: str
    evidence: list[InsightEvidence] = Field(default_factory=list)
    entities: list[InsightEntity] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.7)
    trigger: str | None = None
    source_event_seq: int | None = None
    provider: Literal["azure_openai", "mock"] = "mock"
    synthetic: bool = True


class CandidateMoment(BaseModel):
    """Detector output before language generation."""

    match_id: str
    match_clock: str
    event_seq: int
    event_id: str
    trigger: str
    priority: Literal["low", "medium", "high"]
    reason: str
    event_type: str
