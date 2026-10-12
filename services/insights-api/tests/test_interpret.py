"""Slice 2 — match state aggregation and state API."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.events import MatchEvent
from app.pipeline.interpret import MatchStateEngine, build_state
from app.synthetic.generator import MATCH_HALF_ID

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN = REPO_ROOT / "data" / "synthetic" / "interpret_golden.json"


def _golden_events() -> tuple[list[MatchEvent], dict]:
    raw = json.loads(GOLDEN.read_text())
    events = [MatchEvent.model_validate(e) for e in raw["events"]]
    return events, raw["expected_final"]


def test_golden_fixture_aggregation() -> None:
    events, expected = _golden_events()
    state = build_state("syn-interpret-golden", events)

    assert state.score == expected["score"]
    assert state.possessing_team_id == expected["possessing_team_id"]
    assert state.synthetic is True

    nb = state.teams["northbridge"]
    assert nb.passes_attempted == expected["northbridge"]["passes_attempted"]
    assert nb.passes_accurate == expected["northbridge"]["passes_accurate"]
    assert nb.pass_accuracy == expected["northbridge"]["pass_accuracy"]
    assert nb.avg_pass_distance_m == expected["northbridge"]["avg_pass_distance_m"]
    assert nb.avg_pass_difficulty == expected["northbridge"]["avg_pass_difficulty"]

    hb = state.teams["harbor"]
    assert hb.shots == expected["harbor"]["shots"]
    assert hb.shots_on_target == expected["harbor"]["shots_on_target"]
    assert hb.tackles == expected["harbor"]["tackles"]
    assert hb.tackles_won == expected["harbor"]["tackles_won"]
    assert hb.goals == expected["harbor"]["goals"]

    assert state.last_pass_quality is not None
    assert state.last_pass_quality.distance_m == expected["last_pass_quality"]["distance_m"]
    assert state.last_pass_quality.accurate == expected["last_pass_quality"]["accurate"]
    assert state.last_pass_quality.difficulty == expected["last_pass_quality"]["difficulty"]

    assert state.pressure.current == expected["pressure_current"]
    assert state.pressure.sample_count >= expected["pressure_sample_count_min"]
    # Rolling 5-minute window drops the kickoff once clock reaches 6:00
    assert state.rhythm.event_count == 7
    assert state.rhythm.tempo in {"slow", "medium", "high"}
    assert round(nb.possession_pct + hb.possession_pct, 1) == 100.0


def test_incremental_apply_matches_apply_all() -> None:
    events, _ = _golden_events()
    engine = MatchStateEngine(match_id="syn-interpret-golden")
    for event in events:
        engine.apply(event)
    assert engine.state.model_dump() == build_state("syn-interpret-golden", events).model_dump()


def test_state_api_half(client: TestClient | None = None) -> None:
    c = client or TestClient(app)
    res = c.get(f"/api/v1/matches/{MATCH_HALF_ID}/state")
    assert res.status_code == 200
    body = res.json()
    assert body["match_id"] == MATCH_HALF_ID
    assert body["synthetic"] is True
    assert "northbridge" in body["teams"] or len(body["teams"]) >= 1
    assert "pressure" in body
    assert "rhythm" in body


def test_state_api_up_to_seq() -> None:
    c = TestClient(app)
    full = c.get(f"/api/v1/matches/{MATCH_HALF_ID}/state").json()
    partial = c.get(
        f"/api/v1/matches/{MATCH_HALF_ID}/state",
        params={"up_to_seq": 10},
    ).json()
    assert partial["last_seq"] <= 10
    assert partial["last_seq"] <= full["last_seq"]


def test_sse_include_state() -> None:
    c = TestClient(app)
    with c.stream(
        "GET",
        "/api/v1/matches/syn-northbridge-harbor-001/stream",
        params={"speed": 10_000, "include_state": True},
    ) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())

    assert "event: match_tick" in body
    data_lines = [
        line[len("data: ") :]
        for line in body.splitlines()
        if line.startswith("data: ") and "complete" not in line
    ]
    first = json.loads(data_lines[0])
    assert "event" in first
    assert "state" in first
    assert first["state"]["synthetic"] is True
