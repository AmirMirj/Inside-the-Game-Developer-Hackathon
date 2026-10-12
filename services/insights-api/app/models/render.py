"""Timed studio / overlay render payloads (Stage D)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.insight import InsightEntity


class RenderText(BaseModel):
    headline: str
    body: str
    why_it_matters: str | None = None


class RenderPayload(BaseModel):
    """Machine-readable overlay contract for studio / graphics path."""

    render_id: UUID
    insight_id: str | None = None
    match_id: str
    match_clock: str
    duration_ms: int = Field(ge=0)
    priority: Literal["low", "medium", "high"]
    overlay_type: Literal["lower_third", "moment_card", "recap_block", "ticker"]
    text: RenderText
    entities: list[InsightEntity] = Field(default_factory=list)
    source_event_seq: int | None = None
    trigger: str | None = None
    confidence: float | None = None
    synthetic: bool = True
