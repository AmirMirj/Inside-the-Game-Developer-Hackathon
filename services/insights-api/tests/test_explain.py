"""Slice 3 — moment detection and explain agent."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.agents.explain_agent import ExplainAgent
from app.agents.llm import MockLlmClient
from app.main import app
from app.models.events import MatchEvent
from app.pipeline.explain import detect_moments, explain_event, scan_insights
from app.pipeline.interpret import MatchStateEngine
from app.pipeline.moments import MomentDetector
from app.synthetic.generator import MATCH_HALF_ID, SAMPLE_MATCH_ID

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN = REPO_ROOT / "data" / "synthetic" / "interpret_golden.json"


def _golden_events() -> list[MatchEvent]:
    raw = json.loads(GOLDEN.read_text())
    return [MatchEvent.model_validate(e) for e in raw["events"]]


def test_detector_flags_shot_goal_pressure_turnover() -> None:
    events = _golden_events()
    moments = detect_moments(events)
    triggers = {m.trigger for m, _, _ in moments}
    assert "shot" in triggers
    assert "goal" in triggers
    assert "pressure_spike" in triggers or "tackle_won" in triggers
    assert "turnover" in triggers or "tackle_won" in triggers


def test_explain_uses_match_state_context() -> None:
    events = _golden_events()
    agent = ExplainAgent(client=MockLlmClient())
    # seq 7 is the goal in golden fixture
    insight = explain_event(events=events, seq=7, agent=agent)
    assert insight.headline
    assert insight.why_it_matters
    assert "0-1" in insight.why_it_matters or "0-1" in insight.body or "score" in insight.why_it_matters.lower()
    assert insight.evidence
    assert insight.evidence[0].event_id
    assert insight.confidence > 0
    assert insight.provider == "mock"
    assert insight.trigger == "goal"
    assert insight.synthetic is True


def test_scan_insights_limit() -> None:
    events = _golden_events()
    agent = ExplainAgent(client=MockLlmClient())
    insights = scan_insights(events, agent=agent, min_priority="low", limit=2)
    assert len(insights) == 2
    assert all(i.why_it_matters for i in insights)


def test_moments_api() -> None:
    client = TestClient(app)
    res = client.get(f"/api/v1/matches/{MATCH_HALF_ID}/moments")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert {"trigger", "priority", "event_seq"} <= set(body[0].keys())


def test_explain_api_and_provider() -> None:
    client = TestClient(app)
    provider = client.get("/api/v1/explain/provider").json()
    assert provider["active_provider"] in {"mock", "azure"}

    moments = client.get(f"/api/v1/matches/{SAMPLE_MATCH_ID}/moments").json()
    # sample has a shot and a goal
    assert moments
    seq = moments[0]["event_seq"]
    res = client.post(f"/api/v1/matches/{SAMPLE_MATCH_ID}/explain/{seq}")
    assert res.status_code == 200
    insight = res.json()
    assert insight["why_it_matters"]
    assert insight["headline"]
    assert insight["evidence"]


def test_explain_non_moment_returns_404() -> None:
    client = TestClient(app)
    # seq 0 is metadata kickoff — not a key moment
    res = client.post(f"/api/v1/matches/{SAMPLE_MATCH_ID}/explain/0")
    assert res.status_code == 404


def test_sse_include_insights() -> None:
    client = TestClient(app)
    with client.stream(
        "GET",
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/stream",
        params={"speed": 10_000, "include_insights": True, "include_state": True},
    ) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())

    assert "event: match_tick" in body
    assert "why_it_matters" in body


def test_detector_ignores_plain_pass() -> None:
    events = _golden_events()
    engine = MatchStateEngine(match_id=events[0].match_id)
    detector = MomentDetector()
    # seq 1 is a normal pass
    for event in events:
        state = engine.apply(event)
        moment = detector.evaluate(event, state)
        if event.seq == 1:
            assert moment is None
            break
