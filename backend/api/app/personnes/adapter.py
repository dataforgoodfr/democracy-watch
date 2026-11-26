"""Lecture des personnes du modèle V3 (personnes, mandats)."""

from duckdb import DuckDBPyConnection

from ..core.database import fetch_all, fetch_one
from ..groupes_politiques.adapter import current_ref
from ..organes.adapter import concurrent_mandates
from .schemas import Personne

COLUMNS = f"""
    p.slug AS uid, p.prenom AS first_name, p.nom AS last_name, p.civilite AS civility,
    p.profession, p.photo_url, {current_ref("p.id")} AS groupe
"""


def ref(alias: str) -> str:
    """STRUCT PersonneRef d'une personne jointe sous `alias` ; NULL sans personne."""
    return (
        f"CASE WHEN {alias}.id IS NOT NULL THEN {{'uid': {alias}.slug, "
        f"'first_name': {alias}.prenom, 'last_name': {alias}.nom}} END"
    )


def list_personnes(
    db: DuckDBPyConnection,
    *,
    organe_uid: str,
    limit: int,
    offset: int,
    groupe_uid: str | None = None,
    current: bool = True,
) -> list[Personne]:
    """Membres de l'organe `organe_uid`, éventuellement restreints à un groupe politique."""
    params = {"organe_uid": organe_uid, "limit": limit, "offset": offset}
    if groupe_uid is None:
        condition = "m.date_fin IS NULL" if current else "true"
        join = ""
    else:
        params["groupe_uid"] = groupe_uid
        condition = f"go.uid = $groupe_uid AND {concurrent_mandates('m', 'g', current=current)}"
        join = """JOIN mandats g ON g.personne_id = m.personne_id
                  JOIN organes go ON go.id = g.organe_id"""
    rows = fetch_all(
        db,
        f"""
        SELECT {COLUMNS} FROM personnes p
        WHERE EXISTS (
            SELECT 1 FROM mandats m JOIN organes mo ON mo.id = m.organe_id {join}
            WHERE m.personne_id = p.id AND mo.uid = $organe_uid AND {condition})
        ORDER BY p.nom, p.prenom, p.id LIMIT $limit OFFSET $offset
        """,
        params,
    )
    return [Personne.model_validate(row) for row in rows]


def get_personne(db: DuckDBPyConnection, uid: str) -> Personne | None:
    row = fetch_one(db, f"SELECT {COLUMNS} FROM personnes p WHERE p.slug = $uid", {"uid": uid})
    return Personne.model_validate(row) if row is not None else None
