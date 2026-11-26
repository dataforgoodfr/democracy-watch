from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from anyio import CancelScope, to_thread
from fastapi import APIRouter, Depends, FastAPI

from .amendements.router import router as amendements_router
from .articles.router import router as articles_router
from .core.config import Settings
from .core.database import open_database
from .core.errors import ERROR_RESPONSES, install_error_handlers
from .core.health import router as health_router
from .core.security import require_access
from .dossiers.router import router as dossiers_router
from .groupes_politiques.router import router as groupes_router
from .organes.router import router as organes_router
from .personnes.router import router as personnes_router
from .search.router import router as search_router
from .textes.router import router as textes_router


def create_app(config: Settings | None = None) -> FastAPI:
    config = config if config is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.database = None
        app.state.meili = None
        try:
            if config.MEILI_URL:
                key = config.MEILI_API_KEY
                app.state.meili = httpx.AsyncClient(
                    base_url=config.MEILI_URL,
                    headers={"Authorization": f"Bearer {key.get_secret_value()}"} if key else {},
                    timeout=config.MEILI_TIMEOUT,
                )
            if config.DATA_PATH:
                # L'ouverture lit le catalogue, éventuellement sur S3 : hors de la boucle.
                app.state.database = await to_thread.run_sync(open_database, config)
            yield
        finally:
            database, app.state.database = app.state.database, None
            meili, app.state.meili = app.state.meili, None
            with CancelScope(shield=True):
                if meili is not None:
                    await meili.aclose()
                if database is not None:
                    database.close()

    app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION, lifespan=lifespan)
    app.state.settings = config
    install_error_handlers(app)
    app.include_router(health_router)
    api = APIRouter(
        prefix="/api/v0", dependencies=[Depends(require_access)], responses=ERROR_RESPONSES
    )
    for router in (
        search_router,
        # Travail législatif, du haut vers le bas de la hiérarchie.
        dossiers_router,
        textes_router,
        articles_router,
        amendements_router,
        # Acteurs.
        organes_router,
        groupes_router,
        personnes_router,
    ):
        api.include_router(router)
    app.include_router(api)
    return app


app = create_app()
