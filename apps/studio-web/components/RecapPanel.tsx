"use client";

import type { MatchRecap, StoryBeat } from "@/lib/types";

type Props = {
  beats: StoryBeat[];
  recap: MatchRecap | null;
  language: "en" | "es";
  onLanguageChange: (lang: "en" | "es") => void;
  onGenerate: () => void;
  loading?: boolean;
};

export function RecapPanel({
  beats,
  recap,
  language,
  onLanguageChange,
  onGenerate,
  loading,
}: Props) {
  return (
    <div className="panel-body">
      <div className="recap-controls">
        <label>
          Recap language
          <select
            value={language}
            onChange={(e) => onLanguageChange(e.target.value as "en" | "es")}
          >
            <option value="en">English (EN)</option>
            <option value="es">Español (ES)</option>
          </select>
        </label>
        <button className="btn" type="button" onClick={onGenerate} disabled={loading}>
          {loading ? "Generating…" : "Generate beats + recap"}
        </button>
      </div>

      {recap ? (
        <article className="recap-card">
          <div className="insight-meta">
            <span className="pill">{recap.language.toUpperCase()}</span>
            <span className="pill">{recap.word_count} words</span>
            <span className="pill">~{recap.estimated_read_seconds}s read</span>
            <span className="pill">
              {recap.score?.home ?? 0}-{recap.score?.away ?? 0}
            </span>
          </div>
          <h3>{recap.title}</h3>
          <p className="recap-body">{recap.body}</p>
          {recap.player_mentions?.length ? (
            <p className="status-line">
              Players: {recap.player_mentions.join(" · ")}
            </p>
          ) : null}
        </article>
      ) : (
        <p className="status-line">
          Generate an automated 60–90s synthetic match recap (EN/ES).
        </p>
      )}

      {beats.length ? (
        <div className="beats-list">
          <h4>In-match story beats</h4>
          {beats.map((beat) => (
            <div key={beat.beat_id} className="beat-row">
              <span className="mono">{beat.match_clock}</span>
              <div>
                <strong>{beat.title}</strong>
                <p>{beat.text}</p>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
