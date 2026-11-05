"""Projection Core des groupes politiques vers le contrat public."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import GroupesPolitiques

from .schemas import PoliticalGroup

source = GroupesPolitiques.__table__.c
projection = select(
    source.id.label("uid"),
    source.slug.label("slug"),
    source.nom.label("name"),
    source.chambre.label("chamber"),
    source.actif.label("active"),
    source.nom_complet.label("full_name"),
    source.nom_court.label("short_name"),
    source.couleur.label("color"),
    source.position.label("political_position"),
    source.legislature.label("legislative_term"),
    source.stats_membres_actifs.label("active_member_count"),
)


async def list_political_groups(
    session: AsyncSession, *, limit: int, offset: int
) -> list[PoliticalGroup]:
    statement = projection.order_by(source.id).limit(limit).offset(offset)
    rows = (await session.execute(statement)).mappings().all()
    return [PoliticalGroup.model_validate(row) for row in rows]


async def get_political_group(session: AsyncSession, uid: str) -> PoliticalGroup | None:
    row = (await session.execute(projection.where(source.id == uid))).mappings().one_or_none()
    return PoliticalGroup.model_validate(row) if row is not None else None
