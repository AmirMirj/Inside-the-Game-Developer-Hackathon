"""Deterministic synthetic match-event generator for Stage A ingest."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid5

from app.models.events import EventActor, EventType, MatchEvent
from app.synthetic.rosters import HARBOR, MATCH_META, NORTHBRIDGE, Player, Team

MATCH_HALF_ID = MATCH_META["match_id"]
SAMPLE_MATCH_ID = "syn-northbridge-harbor-001"
_EVENT_NS = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def _event_id(match_id: str, seed: int, seq: int) -> UUID:
    return uuid5(_EVENT_NS, f"{match_id}:{seed}:{seq}")

_EVENT_WEIGHTS: list[tuple[str, int]] = [
    ("pass", 55),
    ("pressure", 12),
    ("tackle", 10),
    ("possession_change", 10),
    ("shot", 8),
    ("foul", 3),
    ("goal", 2),
]


def _clock(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes}:{secs:02d}"


def _clock_to_seconds(match_clock: str) -> int:
    minutes, seconds = match_clock.split(":")
    return int(minutes) * 60 + int(seconds)


def _pick(team: Team, rng: random.Random) -> Player:
    return rng.choice(team.players)


def _other(team_id: str) -> Team:
    return HARBOR if team_id == NORTHBRIDGE.team_id else NORTHBRIDGE


def _team_by_id(team_id: str) -> Team:
    return NORTHBRIDGE if team_id == NORTHBRIDGE.team_id else HARBOR


def generate_half(
    *,
    match_id: str = MATCH_HALF_ID,
    seed: int = 42,
    half_minutes: int = 45,
    target_events: int = 200,
    kickoff: datetime | None = None,
) -> list[MatchEvent]:
    """
    Generate an ordered synthetic first-half event list.

    Default ~200 events across 45 match minutes.
    At stream speed 6 (match-seconds per wall-second), wall time ≈ 7.5 minutes.
    """
    rng = random.Random(seed)
    start = kickoff or datetime(2026, 10, 12, 18, 0, tzinfo=timezone.utc)
    half_seconds = half_minutes * 60

    possessing = NORTHBRIDGE.team_id
    score = {"home": 0, "away": 0}
    events: list[MatchEvent] = []

    def emit(
        seq: int,
        clock_sec: int,
        event_type: EventType,
        *,
        team_id: str | None,
        player_id: str | None,
        actors: list[EventActor],
        payload: dict,
    ) -> MatchEvent:
        return MatchEvent(
            event_id=_event_id(match_id, seed, seq),
            match_id=match_id,
            seq=seq,
            match_clock=_clock(clock_sec),
            period=1,
            type=event_type,
            team_id=team_id,
            player_id=player_id,
            actors=actors,
            payload=payload,
            ts=start + timedelta(seconds=clock_sec),
            synthetic=True,
        )

    events.append(
        emit(
            0,
            0,
            EventType.metadata,
            team_id=None,
            player_id=None,
            actors=[],
            payload={
                "kickoff": True,
                "score": dict(score),
                "home_team_id": NORTHBRIDGE.team_id,
                "away_team_id": HARBOR.team_id,
                "label": MATCH_META["label"],
            },
        )
    )

    span = half_seconds - 30
    slots = sorted(rng.randint(15, span) for _ in range(max(1, target_events - 2)))
    kinds = [k for k, w in _EVENT_WEIGHTS for _ in range(w)]

    seq = 1
    for clock_sec in slots:
        kind = rng.choice(kinds)
        team = _team_by_id(possessing)
        opp = _other(possessing)

        if kind == "pass":
            a = _pick(team, rng)
            b = _pick(team, rng)
            while b.player_id == a.player_id and len(team.players) > 1:
                b = _pick(team, rng)
            accurate = rng.random() > 0.18
            distance = round(rng.uniform(5.0, 45.0), 1)
            difficulty = round(min(0.95, distance / 50.0 + rng.uniform(0, 0.35)), 2)
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.pass_,
                    team_id=team.team_id,
                    player_id=a.player_id,
                    actors=[
                        EventActor(
                            role="passer",
                            player_id=a.player_id,
                            team_id=team.team_id,
                            name=a.name,
                        ),
                        EventActor(
                            role="receiver",
                            player_id=b.player_id,
                            team_id=team.team_id,
                            name=b.name,
                        ),
                    ],
                    payload={
                        "to_player_id": b.player_id,
                        "distance_m": distance,
                        "accurate": accurate,
                        "difficulty": difficulty,
                    },
                )
            )
            if not accurate and rng.random() < 0.55:
                possessing = opp.team_id

        elif kind == "pressure":
            presser = _pick(opp, rng)
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.pressure,
                    team_id=opp.team_id,
                    player_id=presser.player_id,
                    actors=[
                        EventActor(
                            role="presser",
                            player_id=presser.player_id,
                            team_id=opp.team_id,
                            name=presser.name,
                        )
                    ],
                    payload={
                        "intensity": round(rng.uniform(0.45, 0.95), 2),
                        "zone": rng.choice(
                            [
                                "midfield",
                                "final_third_home",
                                "final_third_away",
                                "wide_left",
                                "wide_right",
                            ]
                        ),
                        "on_team_id": possessing,
                    },
                )
            )

        elif kind == "tackle":
            tackler = _pick(opp, rng)
            carrier = _pick(team, rng)
            won = rng.random() > 0.4
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.tackle,
                    team_id=opp.team_id,
                    player_id=tackler.player_id,
                    actors=[
                        EventActor(
                            role="tackler",
                            player_id=tackler.player_id,
                            team_id=opp.team_id,
                            name=tackler.name,
                        ),
                        EventActor(
                            role="carrier",
                            player_id=carrier.player_id,
                            team_id=team.team_id,
                            name=carrier.name,
                        ),
                    ],
                    payload={
                        "won": won,
                        "zone": rng.choice(["midfield", "defensive_third"]),
                    },
                )
            )
            if won:
                possessing = opp.team_id

        elif kind == "possession_change":
            winner = opp
            new_holder = _pick(winner, rng)
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.possession_change,
                    team_id=winner.team_id,
                    player_id=new_holder.player_id,
                    actors=[
                        EventActor(
                            role="gains_possession",
                            player_id=new_holder.player_id,
                            team_id=winner.team_id,
                            name=new_holder.name,
                        )
                    ],
                    payload={
                        "from_team_id": possessing,
                        "reason": rng.choice(
                            [
                                "tackle_pressure",
                                "interception",
                                "loose_ball",
                                "incomplete_pass",
                            ]
                        ),
                    },
                )
            )
            possessing = winner.team_id

        elif kind == "shot":
            shooter = _pick(team, rng)
            on_target = rng.random() > 0.45
            if not on_target:
                outcome = "wide"
            elif rng.random() > 0.35:
                outcome = "saved"
            else:
                outcome = "blocked"
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.shot,
                    team_id=team.team_id,
                    player_id=shooter.player_id,
                    actors=[
                        EventActor(
                            role="shooter",
                            player_id=shooter.player_id,
                            team_id=team.team_id,
                            name=shooter.name,
                        )
                    ],
                    payload={
                        "xg": round(rng.uniform(0.03, 0.45), 2),
                        "on_target": on_target,
                        "shot_speed_kmh": round(rng.uniform(70.0, 120.0), 1),
                        "body_part": rng.choice(["right_foot", "left_foot", "header"]),
                        "outcome": outcome,
                    },
                )
            )

        elif kind == "foul":
            offender = _pick(opp, rng)
            victim = _pick(team, rng)
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.foul,
                    team_id=opp.team_id,
                    player_id=offender.player_id,
                    actors=[
                        EventActor(
                            role="offender",
                            player_id=offender.player_id,
                            team_id=opp.team_id,
                            name=offender.name,
                        ),
                        EventActor(
                            role="fouled",
                            player_id=victim.player_id,
                            team_id=team.team_id,
                            name=victim.name,
                        ),
                    ],
                    payload={"card": None},
                )
            )

        else:  # goal
            scorer = _pick(team, rng)
            assister = _pick(team, rng)
            while assister.player_id == scorer.player_id and len(team.players) > 1:
                assister = _pick(team, rng)
            if team.team_id == NORTHBRIDGE.team_id:
                score["home"] += 1
            else:
                score["away"] += 1
            events.append(
                emit(
                    seq,
                    clock_sec,
                    EventType.goal,
                    team_id=team.team_id,
                    player_id=scorer.player_id,
                    actors=[
                        EventActor(
                            role="scorer",
                            player_id=scorer.player_id,
                            team_id=team.team_id,
                            name=scorer.name,
                        ),
                        EventActor(
                            role="assist",
                            player_id=assister.player_id,
                            team_id=team.team_id,
                            name=assister.name,
                        ),
                    ],
                    payload={
                        "assist_player_id": assister.player_id,
                        "xg": round(rng.uniform(0.15, 0.55), 2),
                        "score_after": dict(score),
                    },
                )
            )
            possessing = opp.team_id

        seq += 1

    events.append(
        emit(
            seq,
            half_seconds,
            EventType.metadata,
            team_id=None,
            player_id=None,
            actors=[],
            payload={"half_time": True, "score": dict(score), "period_ended": 1},
        )
    )

    events.sort(key=lambda e: (_clock_to_seconds(e.match_clock), e.seq))
    return [
        ev.model_copy(
            update={"seq": i, "event_id": _event_id(match_id, seed, i)}
        )
        for i, ev in enumerate(events)
    ]


def list_synthetic_matches() -> list[dict]:
    return [
        {
            "match_id": SAMPLE_MATCH_ID,
            "label": "Northbridge FC vs Harbor FC (short sample)",
            "synthetic": True,
            "streamable": True,
            "kind": "fixture",
        },
        {
            "match_id": MATCH_HALF_ID,
            "label": MATCH_META["label"],
            "synthetic": True,
            "streamable": True,
            "kind": "generated_half",
            "half_minutes": MATCH_META["half_minutes"],
            "default_speed": 6.0,
            "approx_wall_minutes_at_default_speed": round(45 / 6.0, 1),
        },
    ]


def event_type_set(events: list[MatchEvent]) -> set[str]:
    return {e.type.value for e in events}
