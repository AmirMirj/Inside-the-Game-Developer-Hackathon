"""Viewer personalization profiles (Stage E)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ViewerModes(BaseModel):
    player_focus: str | None = None
    metric_focus: str | None = None


class ViewerProfile(BaseModel):
    profile_id: str
    role: Literal["fan", "analyst", "studio"]
    language: str = "en"
    favorite_club_ids: list[str] = Field(default_factory=list)
    favorite_player_ids: list[str] = Field(default_factory=list)
    modes: ViewerModes = Field(default_factory=ViewerModes)


def default_fan_profile(
    *,
    favorite_club_id: str = "northbridge",
    favorite_player_id: str | None = "nb-9",
    player_focus: str | None = None,
) -> ViewerProfile:
    return ViewerProfile(
        profile_id="default-fan",
        role="fan",
        language="en",
        favorite_club_ids=[favorite_club_id] if favorite_club_id else [],
        favorite_player_ids=[favorite_player_id] if favorite_player_id else [],
        modes=ViewerModes(player_focus=player_focus or favorite_player_id),
    )


def default_analyst_profile(
    *,
    metric_focus: str | None = "pressure",
) -> ViewerProfile:
    return ViewerProfile(
        profile_id="default-analyst",
        role="analyst",
        language="en",
        favorite_club_ids=[],
        favorite_player_ids=[],
        modes=ViewerModes(metric_focus=metric_focus),
    )


def default_studio_profile() -> ViewerProfile:
    return ViewerProfile(
        profile_id="default-studio",
        role="studio",
        language="en",
    )
