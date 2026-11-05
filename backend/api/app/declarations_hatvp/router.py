from fastapi import APIRouter, HTTPException

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import HatvpDeclaration

router = APIRouter(prefix="/declarations_hatvp", tags=["Déclarations HATVP"])


@router.get("", summary="Lister les déclarations HATVP")
async def list_hatvp_declarations(
    session: DbSession, pagination: PaginationQuery
) -> Page[HatvpDeclaration]:
    items = await adapter.list_hatvp_declarations(
        session, limit=pagination.limit + 1, offset=pagination.offset
    )
    return Page[HatvpDeclaration].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter une déclaration HATVP")
async def get_hatvp_declaration(uid: str, session: DbSession) -> HatvpDeclaration:
    item = await adapter.get_hatvp_declaration(session, uid)
    if item is None:
        raise HTTPException(404, "Déclaration HATVP introuvable")
    return item
