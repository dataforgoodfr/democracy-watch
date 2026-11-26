"""Lecture des amendements du modèle V3 (table amendements)."""

from duckdb import DuckDBPyConnection

from ..articles.adapter import public_uid as article_public_uid
from ..articles.adapter import ref as article_ref
from ..core.database import fetch_all, fetch_one
from ..dossiers.adapter import ref as dossier_ref
from ..groupes_politiques.adapter import ref as groupe_ref
from ..organes.adapter import ref as organe_ref
from ..personnes.adapter import ref as personne_ref
from ..textes.adapter import ref as texte_ref
from .schemas import Amendement

COLUMNS = f"""
    a.uid, a.numero AS number, {dossier_ref("d")} AS dossier, {texte_ref("t")} AS texte,
    {article_ref("ar", "t")} AS article, a.article_vise AS targeted_article,
    a.alinea_numero AS paragraph_number, parent.uid AS parent_uid,
    {organe_ref("oe")} AS examining_organe, {personne_ref("au")} AS author,
    {organe_ref("ao")} AS author_organe, {groupe_ref("gpo", "gp")} AS groupe,
    a.statut AS status, a.denouement AS outcome, a.motif_denouement AS outcome_reason,
    a.date_depot AS submitted_on, a.date_denouement AS outcome_at,
    a.dispositif AS body, a.expose_sommaire AS explanation
"""
FROM = """amendements a
    JOIN textes t ON t.id = a.texte_id
    JOIN dossiers d ON d.id = a.dossier_id
    LEFT JOIN articles ar ON ar.id = a.article_id
    LEFT JOIN amendements parent ON parent.id = a.parent_id
    LEFT JOIN organes oe ON oe.id = a.organe_examen_id
    LEFT JOIN personnes au ON au.id = a.auteur_id
    LEFT JOIN organes ao ON ao.id = a.auteur_organe_id
    LEFT JOIN groupes_politiques gp ON gp.organe_id = a.groupe_id
    LEFT JOIN organes gpo ON gpo.id = a.groupe_id"""


def list_amendements(
    db: DuckDBPyConnection,
    *,
    dossier_uid: str,
    texte_uid: str,
    limit: int,
    offset: int,
    article_uid: str | None = None,
) -> list[Amendement]:
    """Amendements d'un texte d'un dossier, éventuellement restreints à un article."""
    where = "d.uid = $dossier_uid AND t.uid = $texte_uid"
    params = {"dossier_uid": dossier_uid, "texte_uid": texte_uid, "limit": limit, "offset": offset}
    if article_uid is not None:
        where += f" AND {article_public_uid('ar', 't')} = $article_uid"
        params["article_uid"] = article_uid
    rows = fetch_all(
        db,
        f"SELECT {COLUMNS} FROM {FROM} WHERE {where} "
        "ORDER BY a.numero_ordre NULLS LAST, a.id LIMIT $limit OFFSET $offset",
        params,
    )
    return [Amendement.model_validate(row) for row in rows]


def get_amendement(db: DuckDBPyConnection, uid: str) -> Amendement | None:
    row = fetch_one(db, f"SELECT {COLUMNS} FROM {FROM} WHERE a.uid = $uid", {"uid": uid})
    return Amendement.model_validate(row) if row is not None else None
