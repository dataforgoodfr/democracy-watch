from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_mapping import Amendements, TextesArticles

from .schemas import Amendement

_columns = Amendements.__table__.c
_projection = select(
    _columns.id.label("uid"),
    _columns.uid.label("source_uid"),
    _columns.numero.label("number"),
    _columns.chambre.label("chamber"),
    _columns.legislature.label("legislative_term"),
    _columns.article_vise.label("targeted_article"),
    _columns.dispositif.label("body"),
    _columns.expose_sommaire.label("explanation"),
    _columns.sort.label("outcome"),
    _columns.date_depot.label("submitted_at"),
    _columns.auteur_libelle.label("author"),
    _columns.texte_ref.label("text_reference"),
    _columns.dossier_id.label("dossier_uid"),
    _columns.parlementaire_id.label("parliamentarian_uid"),
    _columns.groupe_ref.label("group_reference"),
    _columns.auteur_ref.label("author_reference"),
    _columns.alinea.label("paragraph"),
    _columns.alinea_numero.label("paragraph_number"),
    _columns.numero_ordre.label("order_number"),
    _columns.amendement_parent_id.label("parent_amendement_uid"),
    _columns.seance_discussion_ref.label("sitting_reference"),
    _columns.id_discussion_commune.label("joint_discussion_id"),
    _columns.id_discussion_identique.label("identical_discussion_id"),
)


_articles = TextesArticles.__table__.c
# Pas de clé vers l'article : « ART. 14 » ou « Article 14 » visent le numéro « 14 » du texte.
# Les amendements « APRÈS ART. 5 » créent un article et ne visent donc aucun article existant.
_targeted_number = func.upper(
    func.regexp_replace(_columns.article_vise, r"^\s*(ART\.|ARTICLE)\s+", "", "i")
)


async def list_amendements(
    session: AsyncSession,
    *,
    dossier_uid: str,
    text_reference: str,
    limit: int,
    offset: int,
    article_uid: str | None = None,
) -> list[Amendement]:
    """Liste les amendements d'un texte d'un dossier, éventuellement restreints à un article."""
    statement = _projection.where(
        _columns.dossier_id == dossier_uid, _columns.texte_ref == text_reference
    )
    if article_uid is not None:
        article = select(_articles.texte_ref, _articles.numero).where(_articles.id == article_uid)
        statement = statement.where(tuple_(_columns.texte_ref, _targeted_number).in_(article))
    statement = statement.order_by(_columns.id).limit(limit).offset(offset)
    result = await session.execute(statement)
    return [Amendement.model_validate(row) for row in result.mappings().all()]


async def get_amendement(session: AsyncSession, uid: str) -> Amendement | None:
    result = await session.execute(_projection.where(_columns.id == uid))
    row = result.mappings().one_or_none()
    return Amendement.model_validate(row) if row is not None else None
