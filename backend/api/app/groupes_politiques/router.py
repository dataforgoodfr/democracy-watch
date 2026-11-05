from fastapi import APIRouter, HTTPException

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import PoliticalGroup

router = APIRouter(prefix="/groupes_politiques", tags=["Groupes politiques"])


@router.get("", summary="Lister les groupes politiques")
async def list_political_groups(
    session: DbSession, pagination: PaginationQuery
) -> Page[PoliticalGroup]:
    items = await adapter.list_political_groups(
        session, limit=pagination.limit + 1, offset=pagination.offset
    )
    return Page[PoliticalGroup].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un groupe politique")
async def get_political_group(uid: str, session: DbSession) -> PoliticalGroup:
    item = await adapter.get_political_group(session, uid)
    if item is None:
        raise HTTPException(404, "Groupe politique introuvable")
    return item
