"""Stage A — Ingest synthetic match events (fixture + live stream)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.agents.explain_agent import get_explain_agent
from app.models.events import MatchEvent
from app.pipeline.interpret import MatchStateEngine
from app.pipeline.moments import MomentDetector
from app.pipeline.render import insight_to_render
from app.synthetic.generator import (
    MATCH_HALF_ID,
    SAMPLE_MATCH_ID,
    generate_half,
    list_synthetic_matches,
)
from app.synthetic.stream import iter_events_paced

router = APIRouter(tags=["ingest"])

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_FIXTURE = REPO_ROOT / "data" / "synthetic" / "sample_match.json"
HALF_FIXTURE = REPO_ROOT / "data" / "synthetic" / "half_northbridge_harbor.json"


def _load_fixture_events(path: Path, match_id: str) -> list[MatchEvent]:
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Synthetic fixture missing: {path.name}")
    raw = json.loads(path.read_text())
    if raw.get("match_id") != match_id:
        raise HTTPException(status_code=404, detail="Unknown synthetic match_id")
    return [MatchEvent.model_validate(e) for e in raw.get("events", [])]


def resolve_events(match_id: str, *, seed: int = 42) -> list[MatchEvent]:
    """Load fixture or generate the accelerated first-half sample."""
    if match_id == SAMPLE_MATCH_ID:
        return _load_fixture_events(DEFAULT_FIXTURE, match_id)
    if match_id == MATCH_HALF_ID:
        if HALF_FIXTURE.exists():
            raw = json.loads(HALF_FIXTURE.read_text())
            if raw.get("match_id") == match_id:
                return [MatchEvent.model_validate(e) for e in raw.get("events", [])]
        return generate_half(match_id=match_id, seed=seed)
    raise HTTPException(status_code=404, detail="Unknown synthetic match_id")


@router.get("/matches")
def list_matches() -> list[dict]:
    return list_synthetic_matches()


@router.get("/matches/{match_id}/events", response_model=list[MatchEvent])
def list_match_events(
    match_id: str,
    seed: int = Query(42, description="RNG seed for generated half"),
) -> list[MatchEvent]:
    return resolve_events(match_id, seed=seed)


@router.get("/matches/{match_id}/stream")
async def stream_match_events_sse(
    match_id: str,
    speed: float = Query(
        6.0,
        gt=0,
        description="Match-clock seconds per wall-clock second (6 ≈ 7.5 min wall for 45 min half)",
    ),
    from_seq: int = Query(0, ge=0),
    seed: int = Query(42),
    include_state: bool = Query(
        False,
        description="If true, each SSE payload includes live match state after the event",
    ),
    include_insights: bool = Query(
        False,
        description="If true, explain key moments (Azure or mock) when detector fires",
    ),
) -> StreamingResponse:
    """Server-Sent Events stream of synthetic match events in order."""
    events = resolve_events(match_id, seed=seed)
    need_engine = include_state or include_insights
    engine = MatchStateEngine(match_id=match_id) if need_engine else None
    detector = MomentDetector() if include_insights else None
    explain = get_explain_agent() if include_insights else None
    recent: list[MatchEvent] = []
    if engine is not None and from_seq > 0:
        for prior in events:
            if prior.seq >= from_seq:
                break
            state = engine.apply(prior)
            recent.append(prior)
            if detector is not None:
                detector.evaluate(prior, state)

    async def event_source():
        async for event in iter_events_paced(events, speed=speed, from_seq=from_seq):
            if engine is None:
                payload = event.model_dump(mode="json")
                yield f"id: {event.seq}\nevent: match_event\ndata: {json.dumps(payload)}\n\n"
                continue

            state = engine.apply(event)
            recent.append(event)
            payload: dict = {
                "event": event.model_dump(mode="json"),
            }
            if include_state:
                payload["state"] = state.model_dump(mode="json")
            if detector is not None and explain is not None:
                moment = detector.evaluate(event, state)
                if moment is not None:
                    insight = explain.explain(
                        moment=moment,
                        event=event,
                        state=state,
                        recent_events=recent,
                    )
                    payload["insight"] = insight.model_dump(mode="json")
                    payload["render"] = insight_to_render(insight).model_dump(mode="json")
            yield (
                f"id: {event.seq}\nevent: match_tick\n"
                f"data: {json.dumps(payload)}\n\n"
            )
        yield 'event: stream_end\ndata: {"status":"complete"}\n\n'

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/matches/{match_id}/ws")
async def stream_match_events_ws(
    websocket: WebSocket,
    match_id: str,
) -> None:
    """WebSocket stream of synthetic match events in order."""
    await websocket.accept()
    try:
        speed_raw = websocket.query_params.get("speed", "6.0")
        from_seq_raw = websocket.query_params.get("from_seq", "0")
        seed_raw = websocket.query_params.get("seed", "42")
        include_state = websocket.query_params.get("include_state", "false").lower() in {
            "1",
            "true",
            "yes",
        }
        include_insights = websocket.query_params.get(
            "include_insights", "false"
        ).lower() in {"1", "true", "yes"}
        speed = float(speed_raw)
        from_seq = int(from_seq_raw)
        seed = int(seed_raw)
        if speed <= 0:
            await websocket.send_json({"error": "speed must be > 0"})
            await websocket.close(code=1008)
            return

        events = resolve_events(match_id, seed=seed)
        need_engine = include_state or include_insights
        engine = MatchStateEngine(match_id=match_id) if need_engine else None
        detector = MomentDetector() if include_insights else None
        explain = get_explain_agent() if include_insights else None
        recent: list[MatchEvent] = []
        await websocket.send_json(
            {
                "type": "stream_start",
                "match_id": match_id,
                "event_count": len(events),
                "speed": speed,
                "include_state": include_state,
                "include_insights": include_insights,
                "synthetic": True,
            }
        )
        async for event in iter_events_paced(events, speed=speed, from_seq=from_seq):
            if engine is None:
                await websocket.send_json(
                    {"type": "match_event", "event": event.model_dump(mode="json")}
                )
                continue

            state = engine.apply(event)
            recent.append(event)
            message: dict = {
                "type": "match_tick",
                "event": event.model_dump(mode="json"),
            }
            if include_state:
                message["state"] = state.model_dump(mode="json")
            if detector is not None and explain is not None:
                moment = detector.evaluate(event, state)
                if moment is not None:
                    insight = explain.explain(
                        moment=moment,
                        event=event,
                        state=state,
                        recent_events=recent,
                    )
                    message["insight"] = insight.model_dump(mode="json")
                    message["render"] = insight_to_render(insight).model_dump(mode="json")
            await websocket.send_json(message)
        await websocket.send_json({"type": "stream_end", "status": "complete"})
    except WebSocketDisconnect:
        return
    except HTTPException as exc:
        await websocket.send_json({"error": exc.detail})
        await websocket.close(code=1008)
    except Exception as exc:  # noqa: BLE001 — surface to client for hackathon debugging
        await websocket.send_json({"error": str(exc)})
        await websocket.close(code=1011)
