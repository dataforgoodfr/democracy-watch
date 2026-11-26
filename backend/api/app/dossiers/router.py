from fastapi import APIRouter, HTTPException

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Dossier

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


@router.get("", response_model=Page[Dossier])
async def list_dossiers(session: DbSession, pagination: PaginationQuery) -> Page[Dossier]:
    items = await adapter.list_dossiers(
        session, limit=pagination.limit + 1, offset=pagination.offset
    )
    return Page[Dossier].from_items(items, pagination)


@router.get("/{dossier_uid}", response_model=Dossier)
async def get_dossier(dossier_uid: str, session: DbSession) -> Dossier:
    item = await adapter.get_dossier(session, dossier_uid)
    if item is None:
        raise HTTPException(404, "Dossier législatif introuvable")
    return item
