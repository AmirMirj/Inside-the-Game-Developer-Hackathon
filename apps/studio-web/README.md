# Studio Web Console

Next.js UI for **Inside the Game** — live synthetic match ingest, state, and Stage D timed overlays.

## Run

1. Start the API on port 8000.
2. In this folder:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Features (Slice 4)

- Live SSE ticker (`include_state` + `include_insights`)
- Match state panel synced to match clock
- Insight / overlay card from `render` payloads
- Replay timeline from `GET /api/v1/matches/{id}/render/timeline`
