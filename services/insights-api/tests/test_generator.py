"""Slice 1 — synthetic generator and stream pacing."""

import asyncio

import pytest

from app.models.events import MatchEvent
from app.synthetic.generator import MATCH_HALF_ID, event_type_set, generate_half
from app.synthetic.stream import iter_events_paced

REQUIRED_TYPES = {
    "pass",
    "shot",
    "tackle",
    "possession_change",
    "pressure",
    "metadata",
}


def test_generate_half_has_required_types_and_fields() -> None:
    events = generate_half(seed=42, target_events=200)
    assert events[0].match_id == MATCH_HALF_ID
    assert events[0].type.value == "metadata"
    assert events[-1].payload.get("half_time") is True

    types = event_type_set(events)
    missing = REQUIRED_TYPES - types
    assert not missing, f"missing event types: {missing}"

    # 45:00 half-time metadata → accelerated demo sample covers a full half
    assert events[-1].match_clock == "45:00"
    assert len(events) >= 100

    for event in events:
        assert event.synthetic is True
        assert event.timestamp == event.ts
        assert event.seq >= 0
        assert isinstance(event.actors, list)
        # Non-metadata play events should name actors
        if event.type.value not in {"metadata"}:
            assert len(event.actors) >= 1


def test_generate_half_is_deterministic() -> None:
    a = generate_half(seed=7, target_events=80)
    b = generate_half(seed=7, target_events=80)
    assert [e.model_dump(mode="json") for e in a] == [e.model_dump(mode="json") for e in b]


def test_events_are_in_sequence_order() -> None:
    events = generate_half(seed=1, target_events=120)
    seqs = [e.seq for e in events]
    assert seqs == list(range(len(events)))


@pytest.mark.asyncio
async def test_paced_stream_preserves_order() -> None:
    events = generate_half(seed=3, target_events=40)
    # Extremely fast playback for unit test
    received: list[MatchEvent] = []
    async for event in iter_events_paced(events, speed=10_000, from_seq=0):
        received.append(event)
    assert [e.seq for e in received] == [e.seq for e in events]


def test_paced_stream_sync_wrapper() -> None:
    events = generate_half(seed=3, target_events=20)

    async def collect() -> list[int]:
        out: list[int] = []
        async for event in iter_events_paced(events, speed=50_000):
            out.append(event.seq)
        return out

    assert asyncio.run(collect()) == [e.seq for e in events]
