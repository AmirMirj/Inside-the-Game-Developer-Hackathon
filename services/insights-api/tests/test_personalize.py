"""Slice 5 — Fan vs Analyst personalization."""

from fastapi.testclient import TestClient

from app.agents.personalize_agent import PersonalizeAgent
from app.main import app
from app.models.profile import default_analyst_profile, default_fan_profile
from app.pipeline.explain import explain_event
from app.pipeline.ingest import resolve_events
from app.pipeline.interpret import MatchStateEngine
from app.synthetic.generator import SAMPLE_MATCH_ID


def _first_moment_bundle():
    events = resolve_events(SAMPLE_MATCH_ID)
    client = TestClient(app)
    moments = client.get(f"/api/v1/matches/{SAMPLE_MATCH_ID}/moments").json()
    assert moments
    seq = moments[0]["event_seq"]
    insight = explain_event(events=events, seq=seq)
    state = MatchStateEngine(match_id=SAMPLE_MATCH_ID).apply_all(
        [e for e in events if e.seq <= seq]
    )
    return insight, state, seq


def test_fan_and_analyst_copy_differ() -> None:
    insight, state, _ = _first_moment_bundle()
    agent = PersonalizeAgent()
    fan = agent.personalize(
        insight=insight,
        profile=default_fan_profile(player_focus="nb-9"),
        state=state,
    )
    analyst = agent.personalize(
        insight=insight,
        profile=default_analyst_profile(metric_focus="pressure"),
        state=state,
    )

    assert fan.text.headline != analyst.text.headline
    assert fan.text.body != analyst.text.body
    assert fan.text.why_it_matters != analyst.text.why_it_matters
    assert "pressure" in (analyst.text.body + analyst.text.why_it_matters).lower() or "rhythm" in (
        analyst.text.body + analyst.text.why_it_matters
    ).lower()
    assert "fan" in fan.text.why_it_matters.lower() or "story" in fan.text.body.lower()


def test_player_focus_biases_fan_copy() -> None:
    insight, state, _ = _first_moment_bundle()
    agent = PersonalizeAgent()
    focused = agent.personalize(
        insight=insight,
        profile=default_fan_profile(
            favorite_club_id="harbor",
            favorite_player_id="hb-10",
            player_focus="hb-10",
        ),
        state=state,
    )
    blob = f"{focused.text.headline} {focused.text.body}".lower()
    assert "player focus" in blob or "hb-10" in blob or "vargas" in blob or "spotlight" in blob


def test_compare_api() -> None:
    client = TestClient(app)
    moments = client.get(f"/api/v1/matches/{SAMPLE_MATCH_ID}/moments").json()
    seq = moments[0]["event_seq"]
    res = client.post(
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/personalize/{seq}/compare",
        params={"favorite_club_id": "northbridge", "player_focus": "nb-9"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["fan"]["text"]["headline"]
    assert body["analyst"]["text"]["headline"]
    assert body["fan"]["text"]["body"] != body["analyst"]["text"]["body"]


def test_default_profiles_api() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/personalize/profiles/defaults")
    assert res.status_code == 200
    body = res.json()
    assert body["fan"]["role"] == "fan"
    assert body["analyst"]["role"] == "analyst"
    assert body["studio"]["role"] == "studio"
