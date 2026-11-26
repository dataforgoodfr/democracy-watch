from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import GroupePolitique

router = APIRouter(prefix="/groupes_politiques", tags=["Groupes politiques"])


@router.get(
    "",
    summary="Lister les groupes politiques",
    description="Avec `organe_uid` : groupes dont au moins un membre siège dans cet organe "
    "(ex. l'Assemblée d'une législature, une commission). `current` : mandats en cours "
    "(par défaut) ou mandats dont les périodes se chevauchent.",
)
def list_groupes(
    db: Db,
    pagination: PaginationQuery,
    organe_uid: str | None = None,
    current: bool = True,
) -> Page[GroupePolitique]:
    items = adapter.list_groupes(
        db,
        organe_uid=organe_uid,
        current=current,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[GroupePolitique].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un groupe politique")
def get_groupe(uid: str, db: Db) -> GroupePolitique:
    item = adapter.get_groupe(db, uid)
    if item is None:
        raise HTTPException(404, "Groupe politique introuvable")
    return item
