"""Projection Core des métadonnées HATVP, sans lecture du contenu XML."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import DeclarationsHatvp

from .schemas import HatvpDeclaration

source = DeclarationsHatvp.__table__.c
projection = select(
    source.id.label("uid"),
    source.parlementaire_id.label("parliamentarian_uid"),
    source.type_document.label("document_type"),
    source.date_depot.label("submitted_at"),
    source.date_publication.label("published_at"),
    source.statut.label("status"),
    source.url_dossier.label("dossier_url"),
)


async def list_hatvp_declarations(
    session: AsyncSession, *, limit: int, offset: int
) -> list[HatvpDeclaration]:
    statement = projection.order_by(source.id).limit(limit).offset(offset)
    rows = (await session.execute(statement)).mappings().all()
    return [HatvpDeclaration.model_validate(row) for row in rows]


async def get_hatvp_declaration(session: AsyncSession, uid: str) -> HatvpDeclaration | None:
    row = (await session.execute(projection.where(source.id == uid))).mappings().one_or_none()
    return HatvpDeclaration.model_validate(row) if row is not None else None
