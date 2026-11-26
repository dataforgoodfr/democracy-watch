"""Connexion à notre base Postgres (copie du dump CLAIR, base partagée).

Paramètres : variables libpq (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD,
PGSSLMODE) ou DATABASE_URL, par exemple chargées depuis le .env :
  uv run --env-file .env python -m democracy_watch.amendements …

Lecture seule par défaut : il faut demander explicitement une connexion en
écriture.
"""

import os

import asyncpg
import psycopg
from psycopg.rows import dict_row


def connect(read_only=True):
    """Connexion psycopg dont les lignes sont des dicts."""
    conn = psycopg.connect(
        os.environ.get("DATABASE_URL", ""),
        connect_timeout=15,
        # faux positif de ty sur les génériques de psycopg (pyright l'accepte)
        row_factory=dict_row,  # ty: ignore[invalid-argument-type]
    )
    conn.read_only = read_only
    return conn


async def connect_async(
    read_only: bool = True,
    *,
    dsn: str | None = None,
    timeout: int = 15,
    command_timeout: int = 15,
) -> asyncpg.Connection:
    """Ouvre une connexion asyncpg ; l'appelant doit ensuite attendre sa fermeture.

    Utilise DATABASE_URL ou les variables PG* natives d'asyncpg. Aucun chargement
    implicite de .env : le programme appelant fournit sa configuration.
    """
    dsn = dsn if dsn is not None else os.environ.get("DATABASE_URL")
    if dsn and dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    return await asyncpg.connect(
        dsn=dsn,
        timeout=timeout,
        command_timeout=command_timeout,
        server_settings={
            "default_transaction_read_only": "on" if read_only else "off",
            "statement_timeout": str(max(1, int(command_timeout * 1000))),
        },
    )
