from fastapi import APIRouter, HTTPException

from ..core.database import Db
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Personne

router = APIRouter(prefix="/personnes", tags=["Personnes"])


@router.get(
    "",
    summary="Lister les membres d'un organe",
    description="`organe_uid` obligatoire (ex. l'Assemblée d'une législature, une commission) ; "
    "`groupe_uid` facultatif restreint aux membres de ce groupe. `current` : mandats en cours "
    "(par défaut) ou mandats dont les périodes se chevauchent.",
)
def list_personnes(
    organe_uid: str,
    db: Db,
    pagination: PaginationQuery,
    groupe_uid: str | None = None,
    current: bool = True,
) -> Page[Personne]:
    items = adapter.list_personnes(
        db,
        organe_uid=organe_uid,
        groupe_uid=groupe_uid,
        current=current,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[Personne].from_items(items, pagination)


@router.get("/{uid}", summary="Consulter une personne", description="`uid` : slug de la personne.")
def get_personne(uid: str, db: Db) -> Personne:
    item = adapter.get_personne(db, uid)
    if item is None:
        raise HTTPException(404, "Personne introuvable")
    return item
