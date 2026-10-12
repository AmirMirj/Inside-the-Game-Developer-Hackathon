# Synthetic football data

All fixtures and generators here are **synthetic and football-realistic**.  
Do **not** treat them as real Premier League match data.

## Files

| File | Purpose |
|------|---------|
| `sample_match.json` | Short fixture for early API/UI checks |
| `half_northbridge_harbor.json` | Full first-half sample (~200 events, 45′ match clock) |
| `interpret_golden.json` | Fixed sequence + expected stats for Stage B tests |

## Regenerate the half

```bash
cd services/insights-api
source .venv/bin/activate
python scripts/export_half.py
```

## Live stream

Prefer the API generator/stream endpoints (Slice 1):

- SSE: `GET /api/v1/matches/syn-northbridge-harbor-half1/stream?speed=6`
- WS: `WS /api/v1/matches/syn-northbridge-harbor-half1/ws?speed=6`

Default `speed=6` finishes the half in about **7.5 wall-clock minutes** (inside the 5–10 minute demo window).
