"""Recherche via Meilisearch : traduction des paramètres de /api/search en requête multi-search.

Les fonctions de construction sont pures (testables sans Meilisearch). Format des filtres
Meilisearch : tableau extérieur = ET, sous-tableau = OU.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Literal, Protocol

SearchType = Literal["amendements", "dossiers", "articles"]
SearchMode = Literal["grouped", "federated"]

# Attributs filtrables par type. Un filtre absent d'un index n'est pas envoyé à cet index.
FILTERABLE = {
    "amendements": (
        "legislature",
        "dossier_uid",
        "texte_ref",
        "groupe_politique",
        "sort",
    ),
    "dossiers": ("legislature", "dossier_uid"),
    "articles": ("legislature", "dossier_uid", "texte_ref"),
}
# Index qui disposent d'un embedder (recherche sémantique).
SEMANTIC = ("amendements",)
# Index portant une date de dépôt (horodatage Unix, en secondes).
DATED = ("amendements", "dossiers")
# Poids dans la recherche fédérée (les dossiers remontent en premier à pertinence égale).
WEIGHTS = {"dossiers": 1.5, "articles": 1.0, "amendements": 1.0}
# Champs surlignés par type.
HIGHLIGHT = {
    "amendements": ["dispositif", "expose"],
    "dossiers": ["titre"],
    "articles": ["contenu"],
}


@dataclass(frozen=True)
class SearchParams:
    """Paramètres de /api/search, déjà validés par la route."""

    q: str = ""
    types: tuple = ("amendements", "dossiers", "articles")
    mode: SearchMode = "grouped"
    semantic_ratio: float = 0.0
    legislature: int | None = None
    dossier_uid: str | None = None
    texte_ref: str | None = None
    groupe_politique: tuple = ()
    sort: tuple = ()
    date_min: date | None = None
    date_max: date | None = None
    facets: tuple = ()
    order: str | None = None
    page: int = 1
    limit: int = 20
    extra_filters: dict = field(default_factory=dict)


def quote(value):
    """Valeur littérale d'un filtre Meilisearch."""
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def any_of(attribute, values):
    """Sous-tableau OU : ``attribute = a`` OU ``attribute = b``."""
    return [f"{attribute} = {quote(value)}" for value in values]


def _timestamp(day, end_of_day=False):
    moment = datetime.combine(
        day, time.max if end_of_day else time.min, tzinfo=timezone.utc
    )
    return int(moment.timestamp())


def build_filters(params, search_type):
    """Filtres applicables à un type de résultat."""
    allowed = FILTERABLE[search_type]
    filters = []
    if params.legislature is not None and "legislature" in allowed:
        filters.append(f"legislature = {int(params.legislature)}")
    for attribute in ("dossier_uid", "texte_ref"):
        value = getattr(params, attribute)
        if value and attribute in allowed:
            filters.append(f"{attribute} = {quote(value)}")
    for attribute in ("groupe_politique", "sort"):
        values = getattr(params, attribute)
        if values and attribute in allowed:
            filters.append(any_of(attribute, values))
    if search_type in DATED:
        if params.date_min:
            filters.append(f"date_depot >= {_timestamp(params.date_min)}")
        if params.date_max:
            filters.append(
                f"date_depot <= {_timestamp(params.date_max, end_of_day=True)}"
            )
    return filters


def build_query(params, search_type, settings):
    """Une requête du multi-search, pour un type de résultat."""
    query = {
        "indexUid": settings.indexes[search_type],
        "q": params.q,
        "attributesToHighlight": HIGHLIGHT[search_type],
        "highlightPreTag": "<mark>",
        "highlightPostTag": "</mark>",
    }
    filters = build_filters(params, search_type)
    if filters:
        query["filter"] = filters
    if params.semantic_ratio > 0 and search_type in SEMANTIC:
        query["hybrid"] = {
            "embedder": settings.meili_embedder,
            "semanticRatio": params.semantic_ratio,
        }
    if params.mode == "federated":
        query["federationOptions"] = {"weight": WEIGHTS[search_type]}
    else:
        query["page"] = params.page
        query["hitsPerPage"] = params.limit
        allowed_facets = [
            facet for facet in params.facets if facet in FILTERABLE[search_type]
        ]
        if allowed_facets:
            query["facets"] = allowed_facets
        if params.order:
            query["sort"] = [params.order]
    return query


def build_request(params, settings):
    """Corps complet de POST /multi-search : ``{"queries": [...], "federation": {...} | None}``."""
    queries = [
        build_query(params, search_type, settings) for search_type in params.types
    ]
    federation = None
    if params.mode == "federated":
        federation = {"limit": params.limit, "offset": (params.page - 1) * params.limit}
        if params.facets:
            federation["facetsByIndex"] = {
                settings.indexes[t]: [f for f in params.facets if f in FILTERABLE[t]]
                for t in params.types
            }
    return {"queries": queries, "federation": federation}


class SearchEngine(Protocol):
    """Moteur de recherche (Meilisearch en production, doublure en test)."""

    def multi_search(self, queries, federation=None): ...

    def health(self): ...


class MeiliSearchEngine:
    """Implémentation Meilisearch (client officiel)."""

    def __init__(self, settings):
        import meilisearch

        self._client = meilisearch.Client(
            settings.meili_url, settings.meili_key or None, timeout=5
        )

    def multi_search(self, queries, federation=None):
        return self._client.multi_search(queries, federation=federation)

    def health(self):
        return self._client.health().get("status") == "available"


def _type_of(index_uid, settings):
    return next(
        (t for t, uid in settings.indexes.items() if uid == index_uid), index_uid
    )


def normalize_response(raw, params, settings):
    """Réponse Meilisearch → réponse de l'API (indépendante des noms d'index)."""
    if params.mode == "federated":
        hits = []
        for hit in raw.get("hits", []):
            federation = hit.pop("_federation", {})
            hits.append(
                {"type": _type_of(federation.get("indexUid", ""), settings), **hit}
            )
        total = raw.get("totalHits", raw.get("estimatedTotalHits", len(hits)))
        return {"mode": "federated", "hits": hits, "total": total, "page": params.page}
    results = {}
    for result in raw.get("results", []):
        search_type = _type_of(result.get("indexUid", ""), settings)
        results[search_type] = {
            "hits": result.get("hits", []),
            "total": result.get("totalHits", result.get("estimatedTotalHits", 0)),
            "facets": result.get("facetDistribution", {}),
        }
    return {"mode": "grouped", "results": results, "page": params.page}


def search(engine, params, settings):
    request = build_request(params, settings)
    raw = engine.multi_search(request["queries"], federation=request["federation"])
    return normalize_response(raw, params, settings)
