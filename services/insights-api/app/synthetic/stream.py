"""Ordered playback of synthetic events for SSE / WebSocket."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence

from app.models.events import MatchEvent


def clock_to_seconds(match_clock: str) -> int:
    minutes, seconds = match_clock.split(":")
    return int(minutes) * 60 + int(seconds)


async def iter_events_paced(
    events: Sequence[MatchEvent],
    *,
    speed: float = 6.0,
    from_seq: int = 0,
) -> AsyncIterator[MatchEvent]:
    """
    Yield events in order, sleeping to respect match-clock gaps.

    `speed` = match-clock seconds advanced per one wall-clock second.
    Default 6.0 → a 45-minute half finishes in ~7.5 wall minutes.
    """
    if speed <= 0:
        raise ValueError("speed must be > 0")

    ordered = [e for e in events if e.seq >= from_seq]
    ordered.sort(key=lambda e: (e.seq, clock_to_seconds(e.match_clock)))

    prev_sec: int | None = None
    for event in ordered:
        clock_sec = clock_to_seconds(event.match_clock)
        if prev_sec is not None:
            gap = max(0.0, (clock_sec - prev_sec) / speed)
            if gap > 0:
                await asyncio.sleep(gap)
        prev_sec = clock_sec
        yield event
