"""API Democracy Watch (voir docs/rfc-proposition-de-endpoints-pour-lapi.md).

Routes : GET /api/v0/search (voir search.py), GET /api/v0/dossiers/{dossier_uid},
GET /api/v0/textes/{texte_ref}/articles, GET /api/v0/amendements/{uid}, GET /health.
Variables d'environnement : DATABASE_URL (voir democracy_watch/db.py) et celles de meili.py.
Lectures Postgres : adaptateur backend/clair.py.

Lancement, depuis la racine du dépôt :
  uv run uvicorn backend.api.app:app --reload
"""

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from meilisearch.errors import MeilisearchError

from backend import clair
from backend.api.meili import client
from backend.api.search import router as search_router

app = FastAPI(title="Democracy Watch API")
app.include_router(search_router)


def found(item, what):
    """Renvoie item, ou une 404 s'il est vide."""
    if not item:
        raise HTTPException(404, f"{what} introuvable")
    return item


@app.get("/api/v0/dossiers/{dossier_uid}")
def get_dossier(dossier_uid: str):
    return found(clair.dossier(dossier_uid), "Dossier")


@app.get("/api/v0/textes/{texte_ref}/articles")
def get_articles(texte_ref: str):
    return found(clair.articles(texte_ref), "Texte")


@app.get("/api/v0/amendements/{uid}")
def get_amendement(uid: str):
    return found(clair.amendement(uid), "Amendement")


@app.get("/health")
def health():
    """État de Postgres et de Meilisearch (503 si l'un des deux ne répond pas)."""
    status = {}
    try:
        clair.ping()
        status["postgres"] = "available"
    except psycopg.Error:
        status["postgres"] = "unavailable"
    try:
        status["meilisearch"] = client.health()["status"]
    except MeilisearchError:
        status["meilisearch"] = "unavailable"
    ok = all(s == "available" for s in status.values())
    return JSONResponse(status, status_code=200 if ok else 503)
