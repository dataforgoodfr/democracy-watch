from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from democracy_watch.api import deps
from democracy_watch.api.main import create_app

DOSSIER = {
    "uid": "DLR5L17N2436",
    "legislature": 17,
    "titre": "Projet de loi d'orientation pour la transition agricole",
    "titre_court": "PJL transition agricole",
    "procedure_libelle": "Projet de loi ordinaire",
    "etat": "en_cours",
    "date_depot": datetime(2026, 9, 3),
    "commissions": [
        {
            "uid": "PO419604",
            "slug": "affaires-economiques",
            "nom": "Affaires économiques",
            "role": "fond",
        }
    ],
    "textes": [{"texte_ref": "PRJLANR5L17B2436", "articles": 6}],
}

AMENDEMENT = {
    "uid": "AMANR5L17PO419604B2436P0D1N000031",
    "numero": "CE31",
    "legislature": 17,
    "chambre": "assemblee",
    "auteur_libelle": "M. Garnier",
    "groupe_ref": "RN",
    "texte_ref": "PRJLANR5L17B2436",
    "article_vise": "Article 3",
    "sort": "Adopté",
    "cosignataires": 3,
}


class FakeRepository:
    def get_dossier(self, uid):
        return DOSSIER if uid == DOSSIER["uid"] else None

    def list_articles(self, texte_ref):
        return [
            {
                "texte_ref": texte_ref,
                "numero": "3",
                "libelle": "Produits phytosanitaires",
                "ordre": 3,
                "contenu": "…",
            }
        ]

    def get_amendement(self, uid):
        return AMENDEMENT if uid == AMENDEMENT["uid"] else None

    def list_amendements(self, texte_ref, article=None, limit=500):
        self.last_call = (texte_ref, article, limit)
        return [AMENDEMENT]

    def ping(self):
        return True


class FakeEngine:
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.calls = []

    def multi_search(self, queries, federation=None):
        self.calls.append((queries, federation))
        return {
            "results": [
                {"indexUid": q["indexUid"], "hits": [], "totalHits": 0} for q in queries
            ]
        }

    def health(self):
        return self.healthy


@pytest.fixture
def repository():
    return FakeRepository()


@pytest.fixture
def engine():
    return FakeEngine()


@pytest.fixture
def client(repository, engine):
    app = create_app()
    app.dependency_overrides[deps.get_repository] = lambda: repository
    app.dependency_overrides[deps.get_search_engine] = lambda: engine
    app.dependency_overrides[deps.get_postgres_probe] = lambda: lambda: True
    return TestClient(app)


def test_dossier(client):
    response = client.get("/api/dossiers/DLR5L17N2436")
    assert response.status_code == 200
    body = response.json()
    assert body["titre_court"] == "PJL transition agricole"
    assert body["commissions"][0]["role"] == "fond"


def test_unknown_dossier_is_404(client):
    assert client.get("/api/dossiers/INCONNU").status_code == 404


def test_articles(client):
    response = client.get("/api/textes/PRJLANR5L17B2436/articles")
    assert response.json()[0]["libelle"] == "Produits phytosanitaires"


def test_amendements_of_an_article(client, repository):
    response = client.get(
        "/api/textes/PRJLANR5L17B2436/amendements", params={"article": "Article 3"}
    )
    assert response.json()[0]["numero"] == "CE31"
    assert repository.last_call == ("PRJLANR5L17B2436", "Article 3", 500)


def test_amendement(client):
    assert (
        client.get(f"/api/amendements/{AMENDEMENT['uid']}").json()["cosignataires"] == 3
    )
    assert client.get("/api/amendements/INCONNU").status_code == 404


def test_search_passes_the_rfc_parameters(client, engine):
    response = client.get(
        "/api/search",
        params=[
            ("q", "retraites"),
            ("types", "amendements"),
            ("types", "dossiers"),
            ("semantic_ratio", "0.5"),
            ("legislature", "17"),
            ("groupe_politique", "RN"),
            ("groupe_politique", "LFI-NFP"),
            ("sort", "Rejeté"),
            ("facets", "groupe_politique"),
            ("order", "date_depot:desc"),
            ("limit", "20"),
        ],
    )
    assert response.status_code == 200
    assert set(response.json()["results"]) == {"amendements", "dossiers"}
    queries, federation = engine.calls[0]
    assert federation is None
    assert queries[0]["filter"][1] == [
        'groupe_politique = "RN"',
        'groupe_politique = "LFI-NFP"',
    ]
    assert queries[0]["sort"] == ["date_depot:desc"]


def test_search_rejects_invalid_parameters(client):
    assert client.get("/api/search", params={"semantic_ratio": 2}).status_code == 422
    assert client.get("/api/search", params={"types": "inconnu"}).status_code == 422
    assert client.get("/api/search", params={"order": "DROP TABLE"}).status_code == 422


def test_limit_is_capped(client, engine):
    client.get("/api/search", params={"limit": 10_000})
    assert engine.calls[0][0][0]["hitsPerPage"] == 100


def test_health_ok(client):
    assert client.get("/health").json() == {
        "status": "ok",
        "postgres": True,
        "meilisearch": True,
    }


def test_health_degraded_when_a_service_is_down(client, engine):
    engine.healthy = False
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_openapi_documents_the_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/api/search",
        "/api/dossiers/{dossier_uid}",
        "/api/textes/{texte_ref}/articles",
        "/api/amendements/{uid}",
        "/health",
    } <= set(paths)
