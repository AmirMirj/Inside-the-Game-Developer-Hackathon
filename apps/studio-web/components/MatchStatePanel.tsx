"use client";

import type { MatchState } from "@/lib/types";

type Props = {
  state: MatchState | null;
  matchClockFallback?: string;
};

export function MatchStatePanel({ state, matchClockFallback = "0:00" }: Props) {
  const clock = state?.match_clock || matchClockFallback;
  const score = state?.score || { home: 0, away: 0 };
  const homeId = state?.home_team_id || "home";
  const awayId = state?.away_team_id || "away";
  const home = state?.teams?.[homeId];
  const away = state?.teams?.[awayId];

  return (
    <div className="panel-body">
      <div className="scoreline" style={{ marginBottom: "1rem" }}>
        <span className="clock">{clock}</span>
        <strong>
          {score.home} – {score.away}
        </strong>
        <span>
          {homeId} vs {awayId}
        </span>
      </div>
      <div className="stat-grid">
        <div className="stat">
          <span>Possession</span>
          <strong>
            {home?.possession_pct ?? 0}% / {away?.possession_pct ?? 0}%
          </strong>
        </div>
        <div className="stat">
          <span>Shots</span>
          <strong>
            {home?.shots ?? 0} / {away?.shots ?? 0}
          </strong>
        </div>
        <div className="stat">
          <span>Pass accuracy</span>
          <strong>
            {home?.pass_accuracy ?? 0}% / {away?.pass_accuracy ?? 0}%
          </strong>
        </div>
        <div className="stat">
          <span>Rhythm</span>
          <strong>{state?.rhythm?.tempo || "—"}</strong>
        </div>
        <div className="stat">
          <span>Pressure</span>
          <strong>{state?.pressure?.current?.toFixed?.(2) ?? "0.00"}</strong>
        </div>
        <div className="stat">
          <span>Possessing</span>
          <strong>{state?.possessing_team_id || "—"}</strong>
        </div>
      </div>
    </div>
  );
}
