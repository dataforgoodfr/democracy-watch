"""Accès en lecture seule à la base DuckDB du modèle V3, locale ou sur S3."""

from collections.abc import Generator
from typing import Annotated, Any

import duckdb
from fastapi import Depends, HTTPException, Request

from .config import Settings

# Nom sous lequel la base est attachée ; chaque curseur s'y place avec USE.
CATALOG = "clair"


def quote(value: str) -> str:
    """Littéral SQL : ATTACH et CREATE SECRET n'acceptent pas de paramètres préparés."""
    return "'" + value.replace("'", "''") + "'"


def open_database(config: Settings) -> duckdb.DuckDBPyConnection:
    """Attache DATA_PATH en lecture seule, après le secret S3 éventuel."""
    if not config.DATA_PATH:
        raise ValueError("DATA_PATH non défini")
    connection = duckdb.connect()
    try:
        if config.S3_ACCESS_KEY_ID and config.S3_SECRET_ACCESS_KEY:
            options = {
                "KEY_ID": config.S3_ACCESS_KEY_ID,
                "SECRET": config.S3_SECRET_ACCESS_KEY.get_secret_value(),
                "REGION": config.S3_REGION,
                "ENDPOINT": config.S3_ENDPOINT,
            }
            values = "".join(f", {k} {quote(v)}" for k, v in options.items() if v)
            connection.execute(f"CREATE SECRET (TYPE s3{values})")
        connection.execute(f"ATTACH {quote(config.DATA_PATH)} AS {CATALOG} (READ_ONLY)")
        # Plus aucun réglage modifiable par une requête après l'ouverture.
        connection.execute("SET lock_configuration = true")
    except BaseException:
        connection.close()
        raise
    return connection


def get_db(request: Request) -> Generator[duckdb.DuckDBPyConnection]:
    """Un curseur par requête : DuckDB n'autorise pas un curseur partagé entre threads."""
    database = request.app.state.database
    if database is None:
        raise HTTPException(503, "Base de données non configurée")
    cursor = database.cursor()
    try:
        cursor.execute(f"USE {CATALOG}")
        yield cursor
    except duckdb.IOException:  # HTTPException (S3) en hérite
        raise HTTPException(503, "Base de données temporairement indisponible") from None
    finally:
        cursor.close()


Db = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


def fetch_all(db: duckdb.DuckDBPyConnection, sql: str, params: Any = None) -> list[dict]:
    """Lignes sous forme de dictionnaires ; les STRUCT deviennent des dictionnaires imbriqués."""
    result = db.execute(sql, params)
    names = [column[0] for column in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchall()]


def fetch_one(db: duckdb.DuckDBPyConnection, sql: str, params: Any = None) -> dict | None:
    rows = fetch_all(db, sql, params)
    return rows[0] if rows else None
