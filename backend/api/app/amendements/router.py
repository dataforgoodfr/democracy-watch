from fastapi import APIRouter, HTTPException

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Amendement

router = APIRouter(prefix="/amendements", tags=["Amendements"])


@router.get("", response_model=Page[Amendement])
async def list_amendements(
    dossier_uid: str,
    text_reference: str,
    session: DbSession,
    pagination: PaginationQuery,
    article_uid: str | None = None,
) -> Page[Amendement]:
    items = await adapter.list_amendements(
        session,
        dossier_uid=dossier_uid,
        text_reference=text_reference,
        article_uid=article_uid,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[Amendement].from_items(items, pagination)


@router.get("/{uid}", response_model=Amendement)
async def get_amendement(uid: str, session: DbSession) -> Amendement:
    item = await adapter.get_amendement(session, uid)
    if item is None:
        raise HTTPException(404, "Amendement introuvable")
    return item
