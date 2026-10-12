"""Validate the synthetic fixture loads into MatchEvent models."""

import json
from pathlib import Path

from app.models.events import MatchEvent

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "data" / "synthetic" / "sample_match.json"


def test_sample_match_events_validate() -> None:
    raw = json.loads(FIXTURE.read_text())
    assert raw["synthetic"] is True
    events = [MatchEvent.model_validate(e) for e in raw["events"]]
    assert len(events) >= 1
    assert all(e.synthetic for e in events)
