"use client";

import type { RenderPayload } from "@/lib/types";

type Props = {
  render: RenderPayload | null;
  modeLabel?: string;
};

export function InsightCard({ render, modeLabel = "Live overlay" }: Props) {
  if (!render) {
    return (
      <div className="insight-card empty">
        <div>
          <strong>No insight on screen</strong>
          <p>Key moments appear here as timed render payloads.</p>
        </div>
      </div>
    );
  }

  return (
    <article className={`insight-card priority-${render.priority}`}>
      <div className="insight-meta">
        <span className="pill">{modeLabel}</span>
        <span className="pill">{render.match_clock}</span>
        <span className="pill">{render.overlay_type}</span>
        <span className="pill">{render.priority}</span>
        <span className="pill">{render.duration_ms} ms</span>
        {render.trigger ? <span className="pill">{render.trigger}</span> : null}
      </div>
      <h3>{render.text.headline}</h3>
      <p>{render.text.body}</p>
      {render.text.why_it_matters ? (
        <p className="why">
          <strong>Why it matters: </strong>
          {render.text.why_it_matters}
        </p>
      ) : null}
      {render.entities?.length ? (
        <p className="status-line">
          Entities:{" "}
          {render.entities
            .map((e) => e.name || e.id)
            .filter(Boolean)
            .join(" · ")}
        </p>
      ) : null}
    </article>
  );
}
