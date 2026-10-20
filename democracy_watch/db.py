"""Connexion à notre base Postgres (copie du dump CLAIR, base partagée).

Paramètres : variables libpq (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD,
PGSSLMODE) ou DATABASE_URL, par exemple chargées depuis le .env :
  uv run --env-file .env python -m democracy_watch.amendements …

Lecture seule par défaut : il faut demander explicitement une connexion en
écriture.
"""

import os

import psycopg
from psycopg.rows import dict_row


def connect(read_only=True):
    """Connexion psycopg dont les lignes sont des dicts."""
    conn = psycopg.connect(
        os.environ.get("DATABASE_URL", ""), connect_timeout=15, row_factory=dict_row
    )
    conn.read_only = read_only
    return conn
