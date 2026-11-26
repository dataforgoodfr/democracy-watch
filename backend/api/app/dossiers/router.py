from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Dossier

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


@router.get(
    "",
    summary="Lister les dossiers législatifs",
    description="Sommet de la hiérarchie législative. Du dépôt le plus récent au plus ancien.",
)
def list_dossiers(db: Db, pagination: PaginationQuery) -> Page[Dossier]:
    items = adapter.list_dossiers(db, limit=pagination.limit + 1, offset=pagination.offset)
    return Page[Dossier].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un dossier législatif")
def get_dossier(uid: str, db: Db) -> Dossier:
    item = adapter.get_dossier(db, uid)
    if item is None:
        raise HTTPException(404, "Dossier législatif introuvable")
    return item
