from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from democracy_watch.api.config import Settings
from democracy_watch.api.deps import get_search_engine, get_settings
from democracy_watch.api.schemas import SearchResponse
from democracy_watch.api.search import SearchParams, search

router = APIRouter(prefix="/api", tags=["recherche"])


@router.get("/search", response_model=SearchResponse, response_model_exclude_none=True)
def search_route(
    settings: Annotated[Settings, Depends(get_settings)],
    engine: Annotated[object, Depends(get_search_engine)],
    q: str = "",
    types: Annotated[
        list[Literal["amendements", "dossiers", "articles"]] | None, Query()
    ] = None,
    mode: Literal["grouped", "federated"] = "grouped",
    semantic_ratio: Annotated[float, Query(ge=0, le=1)] = 0.0,
    legislature: int | None = None,
    dossier_uid: str | None = None,
    texte_ref: str | None = None,
    groupe_politique: Annotated[list[str] | None, Query()] = None,
    sort: Annotated[
        list[str] | None, Query(description="Sort de l'amendement : Adopté, Rejeté…")
    ] = None,
    date_min: date | None = None,
    date_max: date | None = None,
    facets: Annotated[list[str] | None, Query()] = None,
    order: Annotated[str | None, Query(pattern=r"^[a-z_]+:(asc|desc)$")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int | None, Query(ge=1)] = None,
):
    """Recherche générique dans les amendements, dossiers et articles (Meilisearch)."""
    params = SearchParams(
        q=q,
        types=tuple(dict.fromkeys(types or ("amendements", "dossiers", "articles"))),
        mode=mode,
        semantic_ratio=semantic_ratio,
        legislature=legislature,
        dossier_uid=dossier_uid,
        texte_ref=texte_ref,
        groupe_politique=tuple(groupe_politique or ()),
        sort=tuple(sort or ()),
        date_min=date_min,
        date_max=date_max,
        facets=tuple(facets or ()),
        order=order,
        page=page,
        limit=min(limit or settings.default_limit, settings.max_limit),
    )
    return search(engine, params, settings)
