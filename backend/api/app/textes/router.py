from fastapi import APIRouter

from ..core.database import DbSession
from ..schemas import Page, PaginationQuery
from . import adapter
from .schemas import Text

router = APIRouter(prefix="/textes", tags=["Textes"])


@router.get(
    "",
    response_model=Page[Text],
    summary="Lister les articles des textes d'un dossier",
    description="Une ligne par article. Ordre stable par référence, position puis identifiant. "
    "Collection vide si le dossier ou la référence est absent.",
)
async def list_texts(
    dossier_uid: str,
    session: DbSession,
    pagination: PaginationQuery,
    text_reference: str | None = None,
) -> Page[Text]:
    items = await adapter.list_texts(
        session,
        dossier_uid=dossier_uid,
        text_reference=text_reference,
        limit=pagination.limit + 1,
        offset=pagination.offset,
    )
    return Page[Text].from_items(items, pagination)
