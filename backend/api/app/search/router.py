from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from . import adapter
from .schemas import SearchQuery, SearchResults

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    response_model=SearchResults,
    summary="Rechercher dans les amendements, dossiers et articles",
    description="Un groupe de résultats par type, dans l'ordre demandé. Les extraits surlignés "
    "sont dans `_formatted` et entourés de `<mark>` ; le reste du texte n'est pas échappé.",
)
async def generic_search(
    params: Annotated[SearchQuery, Query()], request: Request
) -> SearchResults:
    client = request.app.state.meili
    if client is None:
        raise HTTPException(503, "Moteur de recherche non configuré")
    try:
        return await adapter.search(client, params)
    except httpx.HTTPError:
        raise HTTPException(503, "Moteur de recherche temporairement indisponible") from None
