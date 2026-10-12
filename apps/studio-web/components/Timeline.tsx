"use client";

import type { RenderPayload } from "@/lib/types";

type Props = {
  items: RenderPayload[];
  activeId: string | null;
  onSelect: (item: RenderPayload) => void;
};

export function Timeline({ items, activeId, onSelect }: Props) {
  if (!items.length) {
    return (
      <p className="status-line">
        Load a render timeline to replay insights along the match clock.
      </p>
    );
  }

  return (
    <div className="timeline">
      <p className="status-line">
        Click a clock mark to replay that overlay on the studio card.
      </p>
      <div className="timeline-track" role="list">
        {items.map((item) => (
          <button
            key={item.render_id}
            type="button"
            className={`timeline-chip${activeId === item.render_id ? " active" : ""}`}
            onClick={() => onSelect(item)}
            title={item.text.headline}
          >
            {item.match_clock}
            <span style={{ opacity: 0.75 }}> · {item.priority}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
