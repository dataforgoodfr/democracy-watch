from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import DossiersLegislatifs

from .schemas import Dossier

_columns = DossiersLegislatifs.__table__.c
_projection = select(
    _columns.id.label("uid"),
    _columns.uid.label("source_uid"),
    _columns.titre.label("title"),
    _columns.legislature.label("legislative_term"),
    _columns.etat.label("status"),
    _columns.procedure_libelle.label("procedure"),
    _columns.date_depot.label("submitted_at"),
    _columns.date_adoption.label("adopted_at"),
    _columns.url_an.label("assembly_url"),
    _columns.url_senat.label("senate_url"),
    _columns.url_legifrance.label("legifrance_url"),
    _columns.loi_numero.label("law_number"),
    _columns.loi_titre.label("law_title"),
    _columns.loi_date_jo.label("law_published_at"),
    _columns.sujet_id.label("subject_uid"),
    _columns.updated_at,
)


async def list_dossiers(session: AsyncSession, *, limit: int, offset: int) -> list[Dossier]:
    statement = _projection.order_by(_columns.id).limit(limit).offset(offset)
    result = await session.execute(statement)
    return [Dossier.model_validate(row) for row in result.mappings().all()]


async def get_dossier(session: AsyncSession, uid: str) -> Dossier | None:
    result = await session.execute(_projection.where(_columns.id == uid))
    row = result.mappings().one_or_none()
    return Dossier.model_validate(row) if row is not None else None
