from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Amendement

router = APIRouter(prefix="/amendements", tags=["Amendements"])


@router.get(
    "",
    summary="Lister les amendements d'un texte",
    description="`dossier_uid` et `texte_uid` obligatoires, `article_uid` facultatif. "
    "Collection vide si le texte n'appartient pas au dossier.",
)
def list_amendements(
    dossier_uid: str,
    texte_uid: str,
    db: Db,
    pagination: PaginationQuery,
    article_uid: str | None = None,
) -> Page[Amendement]:
    items = adapter.list_amendements(
        db,
        dossier_uid=dossier_uid,
        texte_uid=texte_uid,
        article_uid=article_uid,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[Amendement].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un amendement")
def get_amendement(uid: str, db: Db) -> Amendement:
    item = adapter.get_amendement(db, uid)
    if item is None:
        raise HTTPException(404, "Amendement introuvable")
    return item
