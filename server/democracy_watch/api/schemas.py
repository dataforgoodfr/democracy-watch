"""Schémas des réponses de l'API (documentés dans l'OpenAPI générée par FastAPI)."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class Commission(BaseModel):
    uid: str
    slug: str
    nom: str
    nom_court: str | None = None
    role: Literal["fond", "avis"] | str


class TexteRef(BaseModel):
    texte_ref: str
    articles: int


class Dossier(BaseModel):
    uid: str
    legislature: int
    titre: str
    titre_court: str | None = None
    procedure_libelle: str | None = None
    etat: str | None = None
    date_depot: datetime | None = None
    date_adoption: datetime | None = None
    url_an: str | None = None
    url_senat: str | None = None
    url_legifrance: str | None = None
    commissions: list[Commission] = []
    textes: list[TexteRef] = []


class Article(BaseModel):
    texte_ref: str
    numero: str
    libelle: str
    ordre: int
    contenu: str
    source_url: str | None = None


class Amendement(BaseModel):
    uid: str
    numero: str
    legislature: int
    chambre: str
    auteur_libelle: str | None = None
    groupe_ref: str | None = None
    texte_ref: str | None = None
    article_vise: str | None = None
    dispositif: str | None = None
    expose_sommaire: str | None = None
    sort: str | None = None
    date_depot: datetime | None = None
    date_sort: datetime | None = None
    source_url: str | None = None
    dossier_uid: str | None = None
    cosignataires: int = 0


class SearchResult(BaseModel):
    hits: list[dict[str, Any]]
    total: int
    facets: dict[str, dict[str, int]] = {}


class SearchResponse(BaseModel):
    """`grouped` : `results` par type ; `federated` : `hits` classés par pertinence."""

    mode: Literal["grouped", "federated"]
    page: int
    results: dict[str, SearchResult] | None = None
    hits: list[dict[str, Any]] | None = None
    total: int | None = None


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    postgres: bool
    meilisearch: bool
