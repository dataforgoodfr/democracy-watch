"""Dépendances FastAPI : configuration, moteur de recherche, dépôt de données.

Les tests les remplacent par des doublures via ``app.dependency_overrides``.
"""

from functools import lru_cache

from democracy_watch.api.config import Settings
from democracy_watch.api.repository import PostgresRepository
from democracy_watch.api.search import MeiliSearchEngine
from democracy_watch.db import connect


@lru_cache
def get_settings():
    return Settings.from_env()


def get_search_engine():
    return MeiliSearchEngine(get_settings())


def get_repository():
    """Une connexion en lecture seule par requête."""
    with connect() as conn:
        yield PostgresRepository(conn)


def ping_postgres():
    with connect() as conn:
        return PostgresRepository(conn).ping()


def get_postgres_probe():
    """Sonde Postgres pour /health : ouvre sa propre connexion, pour signaler une panne sans erreur 500."""
    return ping_postgres
