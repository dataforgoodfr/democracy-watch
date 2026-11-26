"""Lecture des textes du modèle V3 (tables textes, periodes_legislatives)."""

from duckdb import DuckDBPyConnection

from ..core.database import fetch_all, fetch_one
from ..dossiers.adapter import ref as dossier_ref
from .schemas import Texte

COLUMNS = f"""
    t.uid, t.nature, t.numero AS number, {dossier_ref("d")} AS dossier, t.chambre AS chamber,
    pl.numero AS term, t.ordre_dossier AS position, t.titre AS title,
    t.date_depot AS submitted_on
"""
FROM = """textes t
    JOIN dossiers d ON d.id = t.dossier_id
    JOIN periodes_legislatives pl ON pl.id = t.periode_legislative_id"""


def ref(alias: str) -> str:
    """STRUCT TexteRef d'un texte joint sous `alias`."""
    return (
        f"CASE WHEN {alias}.id IS NOT NULL THEN {{'uid': {alias}.uid, "
        f"'nature': {alias}.nature, 'number': {alias}.numero}} END"
    )


def list_textes(
    db: DuckDBPyConnection, *, limit: int, offset: int, dossier_uid: str | None = None
) -> list[Texte]:
    """Textes, dans l'ordre de la navette de chaque dossier."""
    where = ""
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if dossier_uid is not None:
        where, params["dossier_uid"] = "WHERE d.uid = $dossier_uid", dossier_uid
    rows = fetch_all(
        db,
        f"SELECT {COLUMNS} FROM {FROM} {where} "
        "ORDER BY d.id, t.ordre_dossier LIMIT $limit OFFSET $offset",
        params,
    )
    return [Texte.model_validate(row) for row in rows]


def get_texte(db: DuckDBPyConnection, uid: str) -> Texte | None:
    row = fetch_one(db, f"SELECT {COLUMNS} FROM {FROM} WHERE t.uid = $uid", {"uid": uid})
    return Texte.model_validate(row) if row is not None else None
