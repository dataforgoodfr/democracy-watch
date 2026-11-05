from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import partial

import httpx
from anyio import CancelScope
from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from democracy_watch.db import connect_async

from .amendements.router import router as amendements_router
from .articles.router import router as articles_router
from .core.config import Settings
from .core.errors import ERROR_RESPONSES, install_error_handlers
from .core.health import router as health_router
from .core.security import require_access
from .declarations_hatvp.router import router as declarations_router
from .dossiers.router import router as dossiers_router
from .groupes_politiques.router import router as groups_router
from .parlementaires.router import router as parliamentarians_router
from .search.router import router as search_router
from .textes.router import router as textes_router


def create_app(config: Settings | None = None) -> FastAPI:
    config = config if config is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        engine = None
        app.state.session_factory = None
        app.state.meili = None
        try:
            if config.MEILI_URL:
                key = config.MEILI_API_KEY
                app.state.meili = httpx.AsyncClient(
                    base_url=config.MEILI_URL,
                    headers={"Authorization": f"Bearer {key.get_secret_value()}"} if key else {},
                    timeout=config.MEILI_TIMEOUT,
                )
            if config.DATABASE_URL:
                engine = create_async_engine(
                    "postgresql+asyncpg://",
                    async_creator=partial(
                        connect_async,
                        dsn=config.DATABASE_URL,
                        read_only=True,
                        timeout=config.DATABASE_TIMEOUT,
                        command_timeout=config.DATABASE_TIMEOUT,
                    ),
                    pool_size=config.DATABASE_POOL_SIZE,
                    max_overflow=0,
                    pool_timeout=config.DATABASE_POOL_TIMEOUT,
                    pool_pre_ping=True,
                )
                app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
            yield
        finally:
            app.state.session_factory = None
            meili, app.state.meili = app.state.meili, None
            with CancelScope(shield=True):
                if meili is not None:
                    await meili.aclose()
                if engine is not None:
                    await engine.dispose()

    app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION, lifespan=lifespan)
    app.state.settings = config
    install_error_handlers(app)
    app.include_router(health_router)
    api = APIRouter(
        prefix="/api/v0", dependencies=[Depends(require_access)], responses=ERROR_RESPONSES
    )
    for router in (
        search_router,
        dossiers_router,
        textes_router,
        amendements_router,
        articles_router,
        parliamentarians_router,
        groups_router,
        declarations_router,
    ):
        api.include_router(router)
    app.include_router(api)
    return app


app = create_app()
