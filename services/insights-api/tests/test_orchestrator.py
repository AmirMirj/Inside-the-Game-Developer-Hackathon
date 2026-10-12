"""Slice 7 — multi-agent orchestrator."""

from fastapi.testclient import TestClient

from app.agents.explain_agent import ExplainAgent
from app.agents.llm import MockLlmClient
from app.agents.orchestrator import MatchIntelligenceOrchestrator
from app.main import app
from app.pipeline.ingest import resolve_events
from app.synthetic.generator import SAMPLE_MATCH_ID


def test_orchestrator_runs_full_pipeline() -> None:
    events = resolve_events(SAMPLE_MATCH_ID)
    orch = MatchIntelligenceOrchestrator(
        explain_agent=ExplainAgent(client=MockLlmClient()),
    )
    result = orch.run(events, min_priority="low", insight_limit=8, include_recap=True)

    step_names = [s.name for s in result.steps]
    assert step_names[:4] == ["interpret", "explain", "narrative", "personalize"]
    assert result.insights
    assert result.story_beats
    assert result.renders
    assert result.personalized["fan"]
    assert result.personalized["analyst"]
    assert result.personalized["fan"][0].text.body != result.personalized["analyst"][0].text.body
    assert result.recap_en is not None
    assert result.recap_es is not None
    assert result.recap_en.body != result.recap_es.body
    assert result.synthetic is True


def test_orchestrate_api() -> None:
    client = TestClient(app)
    graph = client.get("/api/v1/orchestrate/graph")
    assert graph.status_code == 200
    assert "explain" in {n["id"] for n in graph.json()["nodes"]}

    res = client.post(
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/orchestrate",
        params={"min_priority": "low", "insight_limit": 5},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["match_id"] == SAMPLE_MATCH_ID
    assert len(body["steps"]) >= 4
    assert body["insights"]
    assert body["personalized"]["fan"]
    assert body["recap_en"]["estimated_read_seconds"] >= 60
