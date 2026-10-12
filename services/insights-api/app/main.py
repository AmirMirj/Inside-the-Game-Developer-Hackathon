"""FastAPI entrypoint — pipeline stages wire in as FEATURES slices land."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline.explain_api import router as explain_router
from app.pipeline.ingest import router as ingest_router
from app.pipeline.narrative_api import router as narrative_router
from app.pipeline.orchestrate_api import router as orchestrate_router
from app.pipeline.personalize_api import router as personalize_router
from app.pipeline.render_api import router as render_router
from app.pipeline.state_api import router as state_router

app = FastAPI(
    title="Inside the Game — Insights API",
    description="Synthetic match intelligence pipeline (ingest → interpret → explain → render → personalize).",
    version="0.7.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(state_router, prefix="/api/v1")
app.include_router(explain_router, prefix="/api/v1")
app.include_router(render_router, prefix="/api/v1")
app.include_router(personalize_router, prefix="/api/v1")
app.include_router(narrative_router, prefix="/api/v1")
app.include_router(orchestrate_router, prefix="/api/v1")


@app.get("/")
def root() -> dict:
    return {
        "service": "Inside the Game — Insights API",
        "data_policy": "synthetic_only",
        "docs": "/docs",
        "health": "/health",
        "matches": "/api/v1/matches",
        "orchestrate": "/api/v1/matches/syn-northbridge-harbor-001/orchestrate",
        "orchestrate_graph": "/api/v1/orchestrate/graph",
        "state_example": "/api/v1/matches/syn-northbridge-harbor-half1/state",
        "moments_example": "/api/v1/matches/syn-northbridge-harbor-half1/moments",
        "render_timeline": "/api/v1/matches/syn-northbridge-harbor-001/render/timeline",
        "personalize_defaults": "/api/v1/personalize/profiles/defaults",
        "narrative_recap_multilang": (
            "/api/v1/matches/syn-northbridge-harbor-001/narrative/recap/multilang"
        ),
        "explain_provider": "/api/v1/explain/provider",
        "sse_example": (
            "/api/v1/matches/syn-northbridge-harbor-half1/stream"
            "?speed=6&include_state=true&include_insights=true"
        ),
        "studio_ui": "http://localhost:3000",
        "demo": "See DEMO.md",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "data_policy": "synthetic_only"}
