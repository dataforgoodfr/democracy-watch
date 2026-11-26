from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Article

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get(
    "",
    summary="Lister les articles d'un dossier",
    description="`dossier_uid` obligatoire, `texte_uid` facultatif. Ordre de la navette, puis "
    "du document. Collection vide si le texte n'appartient pas au dossier.",
)
def list_articles(
    dossier_uid: str, db: Db, pagination: PaginationQuery, texte_uid: str | None = None
) -> Page[Article]:
    items = adapter.list_articles(
        db,
        dossier_uid=dossier_uid,
        texte_uid=texte_uid,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[Article].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un article")
def get_article(uid: str, db: Db) -> Article:
    item = adapter.get_article(db, uid)
    if item is None:
        raise HTTPException(404, "Article introuvable")
    return item
