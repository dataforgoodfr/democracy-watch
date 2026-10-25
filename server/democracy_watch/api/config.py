"""Configuration de l'API, lue dans les variables d'environnement."""

import os
from dataclasses import dataclass, field


def _list(value):
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Paramètres de l'API. Valeurs par défaut adaptées au développement local."""

    meili_url: str = "http://localhost:7700"
    meili_key: str = ""
    meili_embedder: str = "hf-t4"
    # Index Meilisearch par type de résultat (paramètre `types` de /api/search).
    indexes: dict = field(
        default_factory=lambda: {
            "amendements": "amendements-2",
            "dossiers": "dossiers",
            "articles": "articles",
        }
    )
    cors_origins: tuple = ("http://localhost:3000",)
    default_limit: int = 20
    max_limit: int = 100

    @classmethod
    def from_env(cls):
        defaults = cls()
        return cls(
            meili_url=os.environ.get("MEILI_URL", defaults.meili_url),
            meili_key=os.environ.get("MEILI_KEY", defaults.meili_key),
            meili_embedder=os.environ.get("MEILI_EMBEDDER", defaults.meili_embedder),
            indexes={
                "amendements": os.environ.get(
                    "MEILI_INDEX_AMENDEMENTS", "amendements-2"
                ),
                "dossiers": os.environ.get("MEILI_INDEX_DOSSIERS", "dossiers"),
                "articles": os.environ.get("MEILI_INDEX_ARTICLES", "articles"),
            },
            cors_origins=tuple(
                _list(
                    os.environ.get("API_CORS_ORIGINS", ",".join(defaults.cors_origins))
                )
            ),
        )
