#!/usr/bin/env python3
"""Export a deterministic synthetic first half into data/synthetic/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.synthetic.generator import MATCH_HALF_ID, generate_half  # noqa: E402
from app.synthetic.rosters import HARBOR, MATCH_META, NORTHBRIDGE  # noqa: E402


def main() -> None:
    events = generate_half(seed=42, target_events=200)
    out = {
        "match_id": MATCH_HALF_ID,
        "label": MATCH_META["label"],
        "competition": MATCH_META["competition"],
        "venue": MATCH_META["venue"],
        "synthetic": True,
        "half_minutes": 45,
        "seed": 42,
        "approx_wall_minutes_at_speed_6": 7.5,
        "teams": {
            "home": {"team_id": NORTHBRIDGE.team_id, "name": NORTHBRIDGE.name},
            "away": {"team_id": HARBOR.team_id, "name": HARBOR.name},
        },
        "players": [
            {
                "player_id": p.player_id,
                "team_id": p.team_id,
                "name": p.name,
                "number": p.number,
            }
            for p in (*NORTHBRIDGE.players, *HARBOR.players)
        ],
        "events": [e.model_dump(mode="json") for e in events],
    }
    dest = ROOT / "data" / "synthetic" / "half_northbridge_harbor.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Wrote {len(events)} events → {dest}")


if __name__ == "__main__":
    main()
