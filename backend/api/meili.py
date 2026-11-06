"""Accès Meilisearch du serveur (repris de demos/server/topics_core.py, sans BERTopic ni LLM).

Variables : MEILI_URL, MEILI_KEY, MEILI_INDEX (défaut amendements-2),
MEILI_EMBEDDER (défaut hf-t4).
"""

import os

import meilisearch

MEILI_URL = os.environ.get("MEILI_URL", "http://localhost:7700").rstrip("/")
MEILI_KEY = os.environ.get("MEILI_KEY")
INDEX = os.environ.get("MEILI_INDEX", "amendements-2")
EMBEDDER = os.environ.get("MEILI_EMBEDDER", "hf-t4")

client = meilisearch.Client(MEILI_URL, MEILI_KEY)


def quote(value):
    """Valeur littérale pour un filtre Meilisearch."""
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'
