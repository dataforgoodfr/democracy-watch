from typing import Annotated

from fastapi import APIRouter, Depends, Response

from democracy_watch.api.deps import get_postgres_probe, get_search_engine
from democracy_watch.api.schemas import Health
from democracy_watch.log import get_logger

router = APIRouter(tags=["santé"])
log = get_logger(__name__)


def _check(name, probe):
    try:
        return bool(probe())
    except Exception:  # noqa: BLE001 — un service injoignable rend l'état « degraded », pas une 500
        log.warning("%s injoignable", name, exc_info=True)
        return False


@router.get("/health", response_model=Health)
def health(
    response: Response,
    postgres_probe: Annotated[object, Depends(get_postgres_probe)],
    engine: Annotated[object, Depends(get_search_engine)],
):
    """État de Postgres et de Meilisearch. 503 si l'un des deux est indisponible."""
    postgres = _check("Postgres", postgres_probe)
    meilisearch = _check("Meilisearch", engine.health)
    ok = postgres and meilisearch
    if not ok:
        response.status_code = 503
    return {
        "status": "ok" if ok else "degraded",
        "postgres": postgres,
        "meilisearch": meilisearch,
    }
