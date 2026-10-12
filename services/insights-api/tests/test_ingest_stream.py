"""Slice 1 — HTTP SSE and WebSocket ingest endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.synthetic.generator import MATCH_HALF_ID, SAMPLE_MATCH_ID


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_list_matches_includes_half(client: TestClient) -> None:
    res = client.get("/api/v1/matches")
    assert res.status_code == 200
    ids = {m["match_id"] for m in res.json()}
    assert SAMPLE_MATCH_ID in ids
    assert MATCH_HALF_ID in ids


def test_list_half_events(client: TestClient) -> None:
    res = client.get(f"/api/v1/matches/{MATCH_HALF_ID}/events", params={"seed": 42})
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 100
    assert events[0]["type"] == "metadata"
    assert "timestamp" in events[0]
    assert "actors" in events[0]
    types = {e["type"] for e in events}
    for required in ("pass", "shot", "tackle", "possession_change", "pressure", "metadata"):
        assert required in types


def test_sse_stream_emits_ordered_events(client: TestClient) -> None:
    # High speed so the test finishes quickly
    with client.stream(
        "GET",
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/stream",
        params={"speed": 10_000},
    ) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())

    assert "event: match_event" in body
    assert "event: stream_end" in body

    data_lines = [
        line[len("data: ") :]
        for line in body.splitlines()
        if line.startswith("data: ") and "complete" not in line
    ]
    payloads = [json.loads(line) for line in data_lines]
    assert payloads
    seqs = [p["seq"] for p in payloads]
    assert seqs == sorted(seqs)


def test_websocket_stream(client: TestClient) -> None:
    with client.websocket_connect(
        f"/api/v1/matches/{SAMPLE_MATCH_ID}/ws?speed=10000"
    ) as ws:
        start = ws.receive_json()
        assert start["type"] == "stream_start"
        assert start["synthetic"] is True

        seqs: list[int] = []
        while True:
            msg = ws.receive_json()
            if msg.get("type") == "stream_end":
                break
            assert msg["type"] == "match_event"
            seqs.append(msg["event"]["seq"])

        assert seqs == sorted(seqs)
        assert len(seqs) >= 1
