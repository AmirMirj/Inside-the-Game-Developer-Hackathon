"""Slice 6 — story beats and multi-language recaps."""

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.ingest import resolve_events
from app.pipeline.narrative import build_beats, build_multilang_recap, build_recap
from app.synthetic.generator import MATCH_HALF_ID, SAMPLE_MATCH_ID


def test_beats_from_sample() -> None:
    events = resolve_events(SAMPLE_MATCH_ID)
    beats = build_beats(events, language="en", min_priority="low")
    assert len(beats) >= 1
    assert beats[0].title
    assert beats[0].text
    assert beats[0].language == "en"
    assert beats[0].synthetic is True


def test_recap_read_window() -> None:
    events = resolve_events(MATCH_HALF_ID)
    recap = build_recap(events, language="en", min_priority="medium", limit=12)
    assert 60 <= recap.estimated_read_seconds <= 90
    assert recap.word_count >= 100
    assert "synthetic" in recap.body.lower() or recap.synthetic is True
    assert recap.milestones


def test_multilang_en_es_differ() -> None:
    events = resolve_events(SAMPLE_MATCH_ID)
    multi = build_multilang_recap(events, languages=("en", "es"), min_priority="low")
    assert set(multi.languages) == {"en", "es"}
    en = multi.recaps["en"]
    es = multi.recaps["es"]
    assert en.body != es.body
    assert en.language == "en"
    assert es.language == "es"
    assert "Resumen" in es.title or "sintético" in es.title.lower() or "sintetico" in es.title.lower()


def test_narrative_api() -> None:
    client = TestClient(app)
    beats = client.get(
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/narrative/beats",
        params={"language": "es", "min_priority": "low"},
    )
    assert beats.status_code == 200
    assert len(beats.json()) >= 1
    assert beats.json()[0]["language"] == "es"

    multi = client.get(
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/narrative/recap/multilang",
        params={"min_priority": "low"},
    )
    assert multi.status_code == 200
    body = multi.json()
    assert "en" in body["recaps"]
    assert "es" in body["recaps"]
    assert body["recaps"]["en"]["estimated_read_seconds"] >= 60
