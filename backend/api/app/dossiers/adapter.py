"""Lecture des dossiers législatifs du modèle V3 (table dossiers)."""

from duckdb import DuckDBPyConnection

from ..core.database import fetch_all, fetch_one
from .schemas import Dossier

COLUMNS = """
    d.uid, d.titre AS title, d.titre_court AS short_title, d.procedure,
    libelle_procedure(d.procedure) AS procedure_label, d.statut AS status,
    d.denouement AS outcome, d.date_depot AS submitted_on, d.date_denouement AS outcome_on,
    CASE WHEN d.denouement = 'promulgue' THEN {
        'number': d.loi_numero, 'title': d.loi_titre, 'published_on': d.loi_date_jo,
        'legifrance_url': d.url_legifrance} END AS loi
"""


def ref(alias: str) -> str:
    """STRUCT DossierRef d'un dossier joint sous `alias`."""
    return (
        f"CASE WHEN {alias}.id IS NOT NULL THEN {{'uid': {alias}.uid, "
        f"'title': {alias}.titre, 'short_title': {alias}.titre_court}} END"
    )


def list_dossiers(db: DuckDBPyConnection, *, limit: int, offset: int) -> list[Dossier]:
    """Dossiers, du dépôt le plus récent au plus ancien."""
    rows = fetch_all(
        db,
        f"SELECT {COLUMNS} FROM dossiers d "
        "ORDER BY d.date_depot DESC NULLS LAST, d.id LIMIT $limit OFFSET $offset",
        {"limit": limit, "offset": offset},
    )
    return [Dossier.model_validate(row) for row in rows]


def get_dossier(db: DuckDBPyConnection, uid: str) -> Dossier | None:
    row = fetch_one(db, f"SELECT {COLUMNS} FROM dossiers d WHERE d.uid = $uid", {"uid": uid})
    return Dossier.model_validate(row) if row is not None else None
