import json

import httpx
import pytest

from backend.api.app.core.config import Settings
from backend.api.app.main import create_app

HIT = {"id": "A1", "_formatted": {"dispositif": "<mark>retraites</mark>"}}


def meili_result(index: str, **extra):
    return {
        "indexUid": index,
        "hits": [HIT],
        "page": 1,
        "hitsPerPage": 20,
        "totalPages": 3,
        "totalHits": 41,
        **extra,
    }


@pytest.fixture
async def meili(application):
    """Remplace le client Meilisearch par un transport simulé qui enregistre les requêtes.

    Pas de monkeypatch : sa restauration supprime l'attribut de `State` au lieu de le remettre.
    """
    requests = []
    responses = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        answer = responses.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    transport = httpx.MockTransport(handle)
    async with httpx.AsyncClient(base_url="http://meili.test", transport=transport) as client:
        application.state.meili = client
        yield requests, responses
        application.state.meili = None


async def test_search_builds_multi_search_payload(client, meili):
    requests, responses = meili
    facets = {"groupe_politique": {"RN": 3}, "sort": {"Rejeté": 2}}
    responses.append(
        httpx.Response(
            200,
            json={
                "results": [
                    meili_result("amendements", facetDistribution=facets),
                    meili_result("dossiers"),
                ]
            },
        )
    )
    response = await client.get(
        "/api/v0/search",
        params=[
            ("q", "retraites"),
            ("types", "amendements"),
            ("types", "dossiers"),
            ("legislature", 17),
            ("groupe_politique", "RN"),
            ("groupe_politique", 'LFI"] OR x'),
            ("outcome", "Rejeté"),
            ("dossier_uid", "D1"),
        ],
    )
    assert response.status_code == 200
    group = {
        "hits": [HIT],
        "page": 1,
        "hits_per_page": 20,
        "total_pages": 3,
        "total_hits": 41,
    }
    assert response.json() == {
        "results": [
            {"type": "amendements", "facets": facets, **group},
            {"type": "dossiers", "facets": {}, **group},
        ]
    }
    [request] = requests
    assert request.url.path == "/multi-search"
    common = {
        "q": "retraites",
        "hybrid": {"embedder": "default", "semanticRatio": 0.5},
        "highlightPreTag": "<mark>",
        "highlightPostTag": "</mark>",
        "page": 1,
        "hitsPerPage": 20,
    }
    assert json.loads(request.content) == {
        "queries": [
            {
                **common,
                "indexUid": "amendements",
                "attributesToHighlight": ["dispositif", "expose"],
                "facets": ["groupe_politique", "sort"],
                "filter": [
                    "legislature = 17",
                    'dossier_id = "D1"',
                    'groupe_politique IN ["RN", "LFI\\"] OR x"]',
                    'sort IN ["Rejet\\u00e9"]',
                ],
            },
            {
                **common,
                "indexUid": "dossiers",
                "attributesToHighlight": ["titre", "loi_titre"],
                "filter": ["legislature = 17", 'id = "D1"'],
            },
        ]
    }


async def test_search_defaults_query_every_type_without_filters(client, meili):
    requests, responses = meili
    results = [meili_result(index) for index in ("amendements", "dossiers", "articles")]
    responses.append(httpx.Response(200, json={"results": results}))
    response = await client.get("/api/v0/search?q=retraites&page=2&hits_per_page=5")
    assert response.status_code == 200
    queries = json.loads(requests[0].content)["queries"]
    assert [query["indexUid"] for query in queries] == ["amendements", "dossiers", "articles"]
    assert queries[2]["attributesToHighlight"] == ["contenu"]
    assert all("filter" not in query for query in queries)
    assert all((query["page"], query["hitsPerPage"]) == (2, 5) for query in queries)


@pytest.mark.parametrize(
    "answer",
    [httpx.Response(500, text="clé privée"), httpx.ConnectError("clé privée")],
)
async def test_search_errors_are_sanitized(client, meili, answer):
    _, responses = meili
    responses.append(answer)
    response = await client.get("/api/v0/search?q=retraites")
    assert response.status_code == response.json()["status"] == 503
    assert "privée" not in response.text


async def test_search_without_meili(client):
    response = await client.get("/api/v0/search?q=retraites")
    assert response.status_code == response.json()["status"] == 503


async def test_meili_client_lifecycle():
    config = Settings(
        _env_file=None,
        DATABASE_URL=None,
        API_PASSWORD=None,
        MEILI_URL="http://meili.test",
        MEILI_API_KEY="cle-locale",  # pragma: allowlist secret
    )
    app = create_app(config)
    async with app.router.lifespan_context(app):
        meili = app.state.meili
        assert meili.base_url == "http://meili.test"
        assert meili.headers["Authorization"] == "Bearer cle-locale"
    assert meili.is_closed
    assert app.state.meili is None
