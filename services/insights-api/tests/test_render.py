"""Slice 4 — render payloads and timeline API."""

from fastapi.testclient import TestClient

from app.agents.explain_agent import ExplainAgent
from app.agents.llm import MockLlmClient
from app.main import app
from app.pipeline.explain import scan_insights
from app.pipeline.ingest import resolve_events
from app.pipeline.render import insight_to_render, insights_to_timeline
from app.synthetic.generator import SAMPLE_MATCH_ID


def test_insight_to_render_contract() -> None:
    events = resolve_events(SAMPLE_MATCH_ID)
    insights = scan_insights(
        events,
        agent=ExplainAgent(client=MockLlmClient()),
        min_priority="low",
        limit=3,
    )
    assert insights
    payload = insight_to_render(insights[0])
    assert payload.match_clock
    assert payload.duration_ms >= 0
    assert payload.priority in {"low", "medium", "high"}
    assert payload.overlay_type
    assert payload.text.headline
    assert payload.text.body
    assert isinstance(payload.entities, list)
    assert payload.synthetic is True


def test_timeline_ordered() -> None:
    events = resolve_events(SAMPLE_MATCH_ID)
    insights = scan_insights(
        events,
        agent=ExplainAgent(client=MockLlmClient()),
        min_priority="low",
        limit=10,
    )
    timeline = insights_to_timeline(insights)
    clocks = [p.match_clock for p in timeline]

    def to_sec(clock: str) -> int:
        m, s = clock.split(":")
        return int(m) * 60 + int(s)

    assert clocks == sorted(clocks, key=to_sec)


def test_render_timeline_api() -> None:
    client = TestClient(app)
    res = client.get(
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/render/timeline",
        params={"use_mock": True, "limit": 10},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    first = body[0]
    assert "match_clock" in first
    assert "duration_ms" in first
    assert "priority" in first
    assert "overlay_type" in first
    assert "text" in first
    assert "headline" in first["text"]
    assert "entities" in first


def test_sse_includes_render_payload() -> None:
    client = TestClient(app)
    with client.stream(
        "GET",
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/stream",
        params={"speed": 10_000, "include_insights": True},
    ) as res:
        body = "".join(res.iter_text())
    assert "why_it_matters" in body
    assert '"overlay_type"' in body
    assert '"text"' in body
