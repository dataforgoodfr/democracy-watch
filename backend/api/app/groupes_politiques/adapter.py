"""Lecture des groupes politiques du modèle V3 (groupes_politiques, sous-type d'organes)."""

from duckdb import DuckDBPyConnection

from ..core.database import fetch_all, fetch_one
from ..organes.adapter import ORGANE_COLUMNS, ORGANE_FROM, concurrent_mandates
from .schemas import GroupePolitique

COLUMNS = f"""{ORGANE_COLUMNS},
    gp.couleur AS color, gp.logo_url, gp.position_politique AS political_position
"""
FROM = f"{ORGANE_FROM} JOIN groupes_politiques gp ON gp.organe_id = o.id"


def ref(organe: str, groupe: str) -> str:
    """STRUCT GroupePolitiqueRef des alias `organe` et `groupe` ; NULL sans groupe."""
    return (
        f"CASE WHEN {groupe}.organe_id IS NOT NULL THEN {{'uid': {organe}.uid, "
        f"'name': {organe}.nom, 'short_name': {organe}.nom_court, 'color': {groupe}.couleur}} END"
    )


def current_ref(personne_id: str) -> str:
    """Sous-requête : groupe du mandat de groupe en cours le plus récent de la personne."""
    return f"""(
        SELECT arg_max({ref("cgo", "cgp")}, cg.date_debut)
        FROM mandats cg
        JOIN groupes_politiques cgp ON cgp.organe_id = cg.organe_id
        JOIN organes cgo ON cgo.id = cg.organe_id
        WHERE cg.personne_id = {personne_id} AND cg.date_fin IS NULL
    )"""


def list_groupes(
    db: DuckDBPyConnection,
    *,
    limit: int,
    offset: int,
    organe_uid: str | None = None,
    current: bool = True,
) -> list[GroupePolitique]:
    """Groupes, ou seulement ceux dont un membre siège dans l'organe `organe_uid`."""
    where = ""
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if organe_uid is not None:
        params["organe_uid"] = organe_uid
        where = f"""WHERE EXISTS (
            SELECT 1 FROM mandats g
            JOIN mandats m ON m.personne_id = g.personne_id
            JOIN organes mo ON mo.id = m.organe_id
            WHERE g.organe_id = gp.organe_id AND mo.uid = $organe_uid
              AND {concurrent_mandates("m", "g", current=current)})"""
    rows = fetch_all(
        db,
        f"SELECT {COLUMNS} FROM {FROM} {where} "
        "ORDER BY o.chambre, o.nom, o.id LIMIT $limit OFFSET $offset",
        params,
    )
    return [GroupePolitique.model_validate(row) for row in rows]


def get_groupe(db: DuckDBPyConnection, uid: str) -> GroupePolitique | None:
    row = fetch_one(db, f"SELECT {COLUMNS} FROM {FROM} WHERE o.uid = $uid", {"uid": uid})
    return GroupePolitique.model_validate(row) if row is not None else None
