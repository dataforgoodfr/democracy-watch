from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Texte

router = APIRouter(prefix="/textes", tags=["Textes"])


@router.get(
    "",
    summary="Lister les textes",
    description="`dossier_uid` facultatif. Ordre de la navette dans chaque dossier.",
)
def list_textes(db: Db, pagination: PaginationQuery, dossier_uid: str | None = None) -> Page[Texte]:
    items = adapter.list_textes(
        db, dossier_uid=dossier_uid, limit=pagination.limit + 1, offset=pagination.offset
    )
    return Page[Texte].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un texte")
def get_texte(uid: str, db: Db) -> Texte:
    item = adapter.get_texte(db, uid)
    if item is None:
        raise HTTPException(404, "Texte introuvable")
    return item
