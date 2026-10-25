"""Application FastAPI. Lancer : ``uv run uvicorn democracy_watch.api.main:app --reload``."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from democracy_watch.api.deps import get_settings
from democracy_watch.api.routers import health, legislatif, search


def create_app():
    settings = get_settings()
    app = FastAPI(
        title="Democracy Watch API",
        version="0.1.0",
        description="Recherche et données législatives pour Democracy Watch.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(search.router)
    app.include_router(legislatif.router)
    app.include_router(health.router)
    return app


app = create_app()
