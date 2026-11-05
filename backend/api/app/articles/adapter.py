"""Lecture et conversion des articles CLAIR vers le contrat public."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import TextesArticles

from .schemas import Article

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


async def list_articles(
    session: AsyncSession,
    *,
    dossier_uid: str,
    limit: int,
    offset: int,
    text_reference: str | None = None,
) -> list[Article]:
    """Liste les articles d'un dossier, éventuellement restreints à une référence de texte."""
    statement = projection.where(source.dossier_id == dossier_uid)
    if text_reference is not None:
        statement = statement.where(source.texte_ref == text_reference)
    else:
        statement = statement.order_by(source.texte_ref)
    statement = statement.order_by(source.ordre, source.id).limit(limit).offset(offset)
    rows = (await session.execute(statement)).mappings().all()
    return [Article.model_validate(row) for row in rows]


async def get_article(session: AsyncSession, uid: str) -> Article | None:
    row = (await session.execute(projection.where(source.id == uid))).mappings().one_or_none()
    return Article.model_validate(row) if row is not None else None
