from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Organe, TypeOrgane

router = APIRouter(prefix="/organes", tags=["Organes"])


# Déclarée avant /{uid} : « types » n'est pas un uid d'organe.
@router.get("/types", summary="Lister les types d'organes")
def list_types(db: Db) -> list[TypeOrgane]:
    return adapter.list_types(db)


@router.get(
    "",
    summary="Lister les organes",
    description="Sommet de la hiérarchie des acteurs. Filtre facultatif par type "
    "(code de `/organes/types`, ex. `COMPER`).",
)
def list_organes(db: Db, pagination: PaginationQuery, type: str | None = None) -> Page[Organe]:
    items = adapter.list_organes(
        db, type=type, limit=pagination.limit + 1, offset=pagination.offset
    )
    return Page[Organe].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter un organe")
def get_organe(uid: str, db: Db) -> Organe:
    item = adapter.get_organe(db, uid)
    if item is None:
        raise HTTPException(404, "Organe introuvable")
    return item
