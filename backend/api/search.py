"""Route GET /api/v0/search : un seul appel /multi-search, avec une requête par type demandé.

Chaque type (amendements ; dossiers quand l'index existera) correspond à un index Meilisearch
et ne reçoit que les filtres, facettes et tris que cet index connaît. La réponse est groupée
par type (pas de fédération) : chaque type a ses résultats, son total et ses facettes.

Filtres : une valeur répétée est un OU (groupe_politique=A&groupe_politique=B), des champs
différents sont combinés en ET. Avec limit=0, la route ne renvoie que totaux et facettes.

Exemples :
  curl 'http://localhost:8000/api/v0/search?q=retraites&legislature=17&facets=sort'
  curl 'http://localhost:8000/api/v0/search?q=retraites&semantic_ratio=0.5'\
'&sort_amendement=Adopté&sort_amendement=Rejeté'
"""

from fastapi import APIRouter, HTTPException, Query, Response
from meilisearch.errors import (
    MeilisearchApiError,
    MeilisearchCommunicationError,
    MeilisearchTimeoutError,
)

from backend.api.meili import EMBEDDER, INDEX, client, quote

router = APIRouter()

# Un type = un index. filters : champs acceptés en paramètre (filtrables dans l'index),
# sortable : champs utilisables dans order. Ajouter ici "dossiers" quand meili_pg_sync le produira.
TYPES = {
    "amendements": {
        "index": INDEX,
        "filters": [
            "legislature",
            "dossier_uid",
            "texte_ref",
            "article",
            "groupe_politique",
            "groupe_libelle",
            "auteur",
            "sort",
        ],
        "sortable": ["date_depot", "updated_at"],
        "highlight": ["dispositif", "expose"],
        "embedder": EMBEDDER,
    },
}
# Les données ne changent qu'à chaque meili_sync ; le cache évite de refaire l'embedding.
CACHE_SECONDS = 60
TYPES_DOC = f"Parmi {', '.join(TYPES)}"


def build_filter(spec, filters):
    """Filtre Meilisearch d'un type, à partir de {champ: [valeurs]} (listes non vides).

    Format attendu par Meilisearch : liste extérieure = ET, sous-liste = OU,
    par ex. ["legislature = 17", ['sort = "Adopté"', 'sort = "Rejeté"']].
    """
    return [
        [f"{field} = {quote(v)}" for v in values]
        for field, values in filters.items()
        if field in spec["filters"]
    ]


def run(queries):
    """multi_search ; si l'embedder ne répond pas, relance sans hybrid.

    Renvoie (résultats, repli).
    """
    try:
        return client.multi_search(queries)["results"], False
    except MeilisearchApiError as err:
        hybrid = any("hybrid" in q for q in queries)
        if not hybrid or "embed" not in f"{err.code} {err.message}".lower():
            raise
    # Un multi_search échoue en entier : on retire hybrid de toutes les requêtes.
    keyword = [{k: v for k, v in q.items() if k != "hybrid"} for q in queries]
    return client.multi_search(keyword)["results"], True


def search_mode(query, result, fell_back):
    """`hybrid` si la partie sémantique a vraiment servi, sinon `keyword`.

    Si l'embedder échoue avec semanticRatio < 1, Meilisearch ne lève pas d'erreur : il
    renvoie les résultats par mots-clés avec semanticHitCount = 0.
    """
    if "hybrid" not in query or fell_back:
        return "keyword"
    if result["hits"] and result.get("semanticHitCount") == 0:
        return "keyword"
    return "hybrid"


@router.get("/api/v0/search")
def search(
    response: Response,
    q: str = "",
    types: list[str] = Query(list(TYPES), description=TYPES_DOC),
    semantic_ratio: float = Query(
        0, ge=0, le=1, description="0 = mots-clés seuls, 1 = sémantique seule"
    ),
    legislature: list[int] = Query([]),
    dossier_uid: list[str] = Query([]),
    texte_ref: list[str] = Query([]),
    article: list[str] = Query([], description='Libellé exact, ex. "Article 3 bis"'),
    groupe_politique: list[str] = Query([], description="uid du groupe (PO...)"),
    groupe_libelle: list[str] = Query([]),
    auteur: list[str] = Query([], description="uid de l'acteur (PA...)"),
    sort: list[str] = Query(
        [], alias="sort_amendement", description="Sort de l'amendement (Adopté, Rejeté…)"
    ),
    facets: list[str] = Query([]),
    order: list[str] = Query([], description="champ:asc ou champ:desc, ex. date_depot:desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=0, le=100),
):
    """Recherche dans les index demandés ; résultats groupés par type.

    `search_mode` vaut `keyword` si la recherche sémantique n'a pas été demandée ou si le
    service d'embedding ne répond pas : la recherche est alors relancée en mots-clés seuls
    (réponse 200).
    """
    types = list(dict.fromkeys(types))
    if unknown := [t for t in types if t not in TYPES]:
        raise HTTPException(400, f"Types inconnus : {unknown}. Valeurs possibles : {list(TYPES)}")
    filters = {
        field: values
        for field, values in {
            "legislature": legislature,
            "dossier_uid": dossier_uid,
            "texte_ref": texte_ref,
            "article": article,
            "groupe_politique": groupe_politique,
            "groupe_libelle": groupe_libelle,
            "auteur": auteur,
            "sort": sort,
        }.items()
        if values
    }

    queries = []
    for name in types:
        spec = TYPES[name]
        query = {
            "indexUid": spec["index"],
            "q": q,
            "filter": build_filter(spec, filters),
            "facets": [f for f in facets if f in spec["filters"]],
            "sort": [o for o in order if o.split(":")[0] in spec["sortable"]],
            # page + hitsPerPage : totalHits exact (limit + offset ne donne qu'une estimation).
            "page": page,
            "hitsPerPage": limit,
        }
        if spec.get("highlight"):
            query |= {
                "attributesToHighlight": spec["highlight"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
            }
        if semantic_ratio > 0 and q and spec.get("embedder"):
            query["hybrid"] = {"embedder": spec["embedder"], "semanticRatio": semantic_ratio}
        queries.append(query)

    try:
        results, fell_back = run(queries)
    except (MeilisearchCommunicationError, MeilisearchTimeoutError) as err:
        raise HTTPException(503, "Meilisearch injoignable") from err
    except MeilisearchApiError as err:
        # 400 : requête invalide (filtre, tri…) ; le reste vient de Meilisearch lui-même.
        raise HTTPException(400 if err.status_code == 400 else 502, err.message) from err

    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return {
        "q": q,
        "results": {
            name: {
                "hits": r["hits"],
                "total": r["totalHits"],
                "page": r["page"],
                "total_pages": r["totalPages"],
                "limit": r["hitsPerPage"],
                "facets": r.get("facetDistribution", {}),
                "search_mode": search_mode(query, r, fell_back),
            }
            for name, query, r in zip(types, queries, results, strict=True)
        },
    }
