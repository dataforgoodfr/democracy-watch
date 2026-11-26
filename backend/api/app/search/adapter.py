"""Traduction de la recherche publique en requêtes multi-search Meilisearch."""

import json

import httpx

from .schemas import SearchGroup, SearchQuery, SearchResults, SearchType

EMBEDDER = "default"
HIGHLIGHT_PRE_TAG = "<mark>"
HIGHLIGHT_POST_TAG = "</mark>"

# Noms d'index et d'attributs Meilisearch, à ne pas utiliser hors de cet adaptateur.
INDEXES: dict[SearchType, str] = {
    "amendements": "amendements",
    "dossiers": "dossiers",
    "articles": "articles",
}
DOSSIER_ATTRIBUTES: dict[SearchType, str] = {
    "amendements": "dossier_id",
    "dossiers": "id",
    "articles": "dossier_id",
}
HIGHLIGHTS: dict[SearchType, list[str]] = {
    "amendements": ["dispositif", "expose"],
    "dossiers": ["titre", "loi_titre"],
    "articles": ["contenu"],
}
FACETS: dict[SearchType, list[str]] = {"amendements": ["groupe_politique", "sort"]}


def any_of(attribute: str, values: list[str]) -> str:
    """Construit un filtre IN ; json.dumps échappe les guillemets des valeurs saisies."""
    return f"{attribute} IN [{', '.join(json.dumps(value) for value in values)}]"


def build_filters(kind: SearchType, query: SearchQuery) -> list[str]:
    filters = []
    if query.legislature is not None:
        filters.append(f"legislature = {query.legislature}")
    if query.dossier_uid is not None:
        filters.append(f"{DOSSIER_ATTRIBUTES[kind]} = {json.dumps(query.dossier_uid)}")
    # Groupes et sorts n'existent que pour les amendements : ignorés ailleurs.
    if kind == "amendements" and query.groupe_politique:
        filters.append(any_of("groupe_politique", query.groupe_politique))
    if kind == "amendements" and query.outcome:
        filters.append(any_of("sort", query.outcome))
    return filters


def build_queries(query: SearchQuery) -> list[dict]:
    queries = []
    for kind in dict.fromkeys(query.types):
        payload = {
            "indexUid": INDEXES[kind],
            "q": query.q,
            "hybrid": {"embedder": EMBEDDER, "semanticRatio": query.semantic_ratio},
            "attributesToHighlight": HIGHLIGHTS[kind],
            "highlightPreTag": HIGHLIGHT_PRE_TAG,
            "highlightPostTag": HIGHLIGHT_POST_TAG,
            "page": query.page,
            "hitsPerPage": query.hits_per_page,
        }
        if filters := build_filters(kind, query):
            payload["filter"] = filters
        if kind in FACETS:
            payload["facets"] = FACETS[kind]
        queries.append(payload)
    return queries


async def search(client: httpx.AsyncClient, query: SearchQuery) -> SearchResults:
    """Interroge /multi-search ; les erreurs httpx sont laissées à l'appelant."""
    queries = build_queries(query)
    response = await client.post("/multi-search", json={"queries": queries})
    response.raise_for_status()
    kinds = {index: kind for kind, index in INDEXES.items()}
    return SearchResults(
        results=[
            SearchGroup(
                type=kinds[result["indexUid"]],
                hits=result["hits"],
                facets=result.get("facetDistribution", {}),
                page=result["page"],
                hits_per_page=result["hitsPerPage"],
                total_pages=result["totalPages"],
                total_hits=result["totalHits"],
            )
            for result in response.json()["results"]
        ]
    )
