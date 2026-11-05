"""Lecture des articles CLAIR d'un dossier, exposés comme lignes de textes."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import TextesArticles

from .schemas import Text

source = TextesArticles.__table__.c
projection = select(
    source.id.label("uid"),
    source.texte_ref.label("text_reference"),
    source.numero.label("number"),
    source.libelle.label("label"),
    source.contenu.label("content"),
    source.ordre.label("position"),
    source.chambre.label("chamber"),
    source.legislature.label("legislative_term"),
    source.dossier_id.label("dossier_uid"),
    source.source_url,
)


async def list_texts(
    session: AsyncSession,
    *,
    dossier_uid: str,
    limit: int,
    offset: int,
    text_reference: str | None = None,
) -> list[Text]:
    """Liste les articles d'un dossier, éventuellement restreints à une référence de texte."""
    statement = projection.where(source.dossier_id == dossier_uid)
    if text_reference is not None:
        statement = statement.where(source.texte_ref == text_reference)
    statement = statement.order_by(source.texte_ref, source.ordre, source.id)
    rows = (await session.execute(statement.limit(limit).offset(offset))).mappings().all()
    return [Text.model_validate(row) for row in rows]
