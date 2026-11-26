"""Projection Core des parlementaires vers le contrat public."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import Parlementaires

from .schemas import Parliamentarian

source = Parlementaires.__table__.c
projection = select(
    source.id.label("uid"),
    source.slug.label("slug"),
    source.prenom.label("first_name"),
    source.nom.label("last_name"),
    source.chambre.label("chamber"),
    source.actif.label("active"),
    source.groupe_id.label("group_uid"),
    source.circonscription_id.label("constituency_uid"),
    source.photo_url.label("photo_url"),
    source.site_web.label("website"),
)


async def list_parliamentarians(
    session: AsyncSession, *, limit: int, offset: int
) -> list[Parliamentarian]:
    statement = projection.order_by(source.id).limit(limit).offset(offset)
    rows = (await session.execute(statement)).mappings().all()
    return [Parliamentarian.model_validate(row) for row in rows]


async def get_parliamentarian(session: AsyncSession, uid: str) -> Parliamentarian | None:
    row = (await session.execute(projection.where(source.id == uid))).mappings().one_or_none()
    return Parliamentarian.model_validate(row) if row is not None else None
