"use client";

import type { MatchEvent } from "@/lib/types";

type Props = {
  events: MatchEvent[];
};

export function EventTicker({ events }: Props) {
  const latest = [...events].reverse().slice(0, 40);

  if (!latest.length) {
    return <p className="status-line">Waiting for synthetic events…</p>;
  }

  return (
    <div className="ticker" aria-live="polite">
      {latest.map((event) => {
        const actor = event.actors?.[0]?.name || event.player_id || "—";
        return (
          <div key={`${event.seq}-${event.event_id}`} className="ticker-row">
            <span className="mono">{event.match_clock}</span>
            <strong>{event.type}</strong>
            <span>
              {event.team_id || "match"} · {actor}
            </span>
          </div>
        );
      })}
    </div>
  );
}
