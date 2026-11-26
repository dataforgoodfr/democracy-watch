from fastapi import APIRouter, HTTPException

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Article

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("", response_model=Page[Article])
async def list_articles(
    dossier_uid: str,
    session: DbSession,
    pagination: PaginationQuery,
    text_reference: str | None = None,
) -> Page[Article]:
    items = await adapter.list_articles(
        session,
        dossier_uid=dossier_uid,
        text_reference=text_reference,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[Article].from_items(items, pagination)


@router.get("/{uid}", response_model=Article)
async def get_article(uid: str, session: DbSession) -> Article:
    article = await adapter.get_article(session, uid)
    if article is None:
        raise HTTPException(404, "Article introuvable")
    return article
