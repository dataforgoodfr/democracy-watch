"""Lecture des articles du modèle V3 (table articles)."""

from duckdb import DuckDBPyConnection

from ..core.database import fetch_all, fetch_one
from ..dossiers.adapter import ref as dossier_ref
from ..textes.adapter import ref as texte_ref
from .schemas import Article


def public_uid(article: str, texte: str) -> str:
    """Identifiant public : les id internes changent à chaque reconstruction de la base."""
    return f"{texte}.uid || '-' || {article}.ordre_place"


COLUMNS = f"""
    {public_uid("a", "t")} AS uid, a.numero AS number, a.libelle AS label,
    {texte_ref("t")} AS texte, {dossier_ref("d")} AS dossier, a.ordre_place AS position,
    a.est_emplacement AS is_placeholder, a.est_supprime AS is_deleted, a.contenu AS content
"""
FROM = """articles a
    JOIN textes t ON t.id = a.texte_id
    JOIN dossiers d ON d.id = t.dossier_id"""


def ref(article: str, texte: str) -> str:
    """STRUCT ArticleRef d'un article joint sous `article`, de texte joint sous `texte`."""
    return (
        f"CASE WHEN {article}.id IS NOT NULL THEN {{'uid': {public_uid(article, texte)}, "
        f"'number': {article}.numero, 'label': {article}.libelle}} END"
    )


def list_articles(
    db: DuckDBPyConnection,
    *,
    dossier_uid: str,
    limit: int,
    offset: int,
    texte_uid: str | None = None,
) -> list[Article]:
    """Articles d'un dossier, éventuellement d'un seul texte, dans l'ordre du document."""
    where = "d.uid = $dossier_uid"
    params = {"dossier_uid": dossier_uid, "limit": limit, "offset": offset}
    if texte_uid is not None:
        where += " AND t.uid = $texte_uid"
        params["texte_uid"] = texte_uid
    rows = fetch_all(
        db,
        f"SELECT {COLUMNS} FROM {FROM} WHERE {where} "
        "ORDER BY t.ordre_dossier, a.ordre_place LIMIT $limit OFFSET $offset",
        params,
    )
    return [Article.model_validate(row) for row in rows]


def get_article(db: DuckDBPyConnection, uid: str) -> Article | None:
    row = fetch_one(
        db, f"SELECT {COLUMNS} FROM {FROM} WHERE {public_uid('a', 't')} = $uid", {"uid": uid}
    )
    return Article.model_validate(row) if row is not None else None
