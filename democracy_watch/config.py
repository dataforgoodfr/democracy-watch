"""Configuration de l'API Democracy Watch par variables d'environnement."""

import os
from dataclasses import dataclass

DEFAULT_MEILISEARCH_URL = "http://localhost:7700"


@dataclass(frozen=True)
class Settings:
    """Paramètres de connexion aux services externes de l'API."""

    meilisearch_url: str = DEFAULT_MEILISEARCH_URL
    meilisearch_api_key: str = ""


def load_settings() -> Settings:
    """Charge la configuration depuis les variables d'environnement."""
    raw_url = os.environ.get("MEILISEARCH_URL", "").strip()
    meilisearch_url = raw_url.rstrip("/") if raw_url else DEFAULT_MEILISEARCH_URL
    meilisearch_api_key = os.environ.get("MEILISEARCH_API_KEY", "").strip()
    return Settings(
        meilisearch_url=meilisearch_url,
        meilisearch_api_key=meilisearch_api_key,
    )
