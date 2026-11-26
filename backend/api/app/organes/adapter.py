"""Lecture des organes du modèle V3 (tables organes, macros libelle_type_organe…)."""

from duckdb import DuckDBPyConnection

from ..core.database import fetch_all, fetch_one
from .schemas import Organe, TypeOrgane

ORGANE_COLUMNS = """
    o.uid, o.type, o.nom AS name, o.nom_court AS short_name,
    libelle_type_organe(o.type) AS type_label, famille_du_type(o.type) AS family,
    o.chambre AS chamber, parent.uid AS parent_uid,
    o.date_debut AS start_date, o.date_fin AS end_date
"""
ORGANE_FROM = "organes o LEFT JOIN organes parent ON parent.id = o.parent_id"


def ref(alias: str) -> str:
    """STRUCT OrganeRef d'un organe joint sous `alias` ; NULL sans organe."""
    return (
        f"CASE WHEN {alias}.id IS NOT NULL THEN {{'uid': {alias}.uid, 'type': {alias}.type, "
        f"'name': {alias}.nom, 'short_name': {alias}.nom_court}} END"
    )


def list_types(db: DuckDBPyConnection) -> list[TypeOrgane]:
    rows = fetch_all(
        db,
        """
        SELECT code, libelle_type_organe(code) AS label, famille_du_type(code) AS family,
               chambre_du_type(code) AS chamber
        FROM (SELECT unnest(enum_range(NULL::type_organe))::VARCHAR AS code)
        """,
    )
    return [TypeOrgane.model_validate(row) for row in rows]


def list_organes(
    db: DuckDBPyConnection, *, limit: int, offset: int, type: str | None = None
) -> list[Organe]:
    where = ""
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if type is not None:
        where, params["type"] = "WHERE o.type::VARCHAR = $type", type
    rows = fetch_all(
        db,
        f"SELECT {ORGANE_COLUMNS} FROM {ORGANE_FROM} {where} "
        "ORDER BY o.type, o.nom, o.id LIMIT $limit OFFSET $offset",
        params,
    )
    return [Organe.model_validate(row) for row in rows]


def get_organe(db: DuckDBPyConnection, uid: str) -> Organe | None:
    row = fetch_one(
        db, f"SELECT {ORGANE_COLUMNS} FROM {ORGANE_FROM} WHERE o.uid = $uid", {"uid": uid}
    )
    return Organe.model_validate(row) if row is not None else None


def concurrent_mandates(a: str, b: str, *, current: bool) -> str:
    """Deux mandats `a` et `b` tous deux en cours, ou dont les périodes se chevauchent."""
    if current:
        return f"{a}.date_fin IS NULL AND {b}.date_fin IS NULL"
    return f"se_chevauchent({a}.date_debut, {a}.date_fin, {b}.date_debut, {b}.date_fin)"
