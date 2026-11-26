from fastapi import APIRouter, HTTPException

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Parliamentarian

router = APIRouter(prefix="/parlementaires", tags=["Parlementaires"])


@router.get("", summary="Lister les parlementaires")
async def list_parliamentarians(
    session: DbSession, pagination: PaginationQuery
) -> Page[Parliamentarian]:
    items = await adapter.list_parliamentarians(
        session, limit=pagination.limit + 1, offset=pagination.offset
    )
    return Page[Parliamentarian].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un parlementaire")
async def get_parliamentarian(uid: str, session: DbSession) -> Parliamentarian:
    item = await adapter.get_parliamentarian(session, uid)
    if item is None:
        raise HTTPException(404, "Parlementaire introuvable")
    return item
