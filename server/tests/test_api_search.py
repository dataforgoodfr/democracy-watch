from datetime import date

from democracy_watch.api.config import Settings
from democracy_watch.api.search import (
    SearchParams,
    any_of,
    build_filters,
    build_request,
    normalize_response,
    quote,
)

SETTINGS = Settings()


def test_any_of_builds_an_or_group():
    assert any_of("groupe_politique", ["RN", "LFI-NFP"]) == [
        'groupe_politique = "RN"',
        'groupe_politique = "LFI-NFP"',
    ]


def test_quote_escapes_quotes():
    assert quote('dit "non"') == '"dit \\"non\\""'


def test_filters_follow_the_rfc_example():
    params = SearchParams(
        q="retraites",
        legislature=17,
        dossier_uid="DLR5L17N12345",
        groupe_politique=("RN", "LFI-NFP"),
        sort=("Adopté", "Rejeté"),
    )
    assert build_filters(params, "amendements") == [
        "legislature = 17",
        'dossier_uid = "DLR5L17N12345"',
        ['groupe_politique = "RN"', 'groupe_politique = "LFI-NFP"'],
        ['sort = "Adopté"', 'sort = "Rejeté"'],
    ]


def test_filters_unknown_to_an_index_are_not_sent():
    params = SearchParams(legislature=17, groupe_politique=("RN",), sort=("Adopté",))
    assert build_filters(params, "dossiers") == ["legislature = 17"]


def test_date_range_becomes_timestamps():
    params = SearchParams(date_min=date(2025, 1, 1), date_max=date(2025, 6, 30))
    assert build_filters(params, "amendements") == [
        "date_depot >= 1735689600",
        "date_depot <= 1751327999",
    ]


def test_grouped_request_paginates_each_index():
    params = SearchParams(
        q="retraites",
        types=("amendements", "dossiers"),
        page=2,
        limit=10,
        facets=("sort",),
    )
    request = build_request(params, SETTINGS)
    assert request["federation"] is None
    amendements, dossiers = request["queries"]
    assert amendements["indexUid"] == "amendements-2"
    assert (amendements["page"], amendements["hitsPerPage"]) == (2, 10)
    assert amendements["facets"] == ["sort"]
    assert "facets" not in dossiers  # « sort » n'est pas filtrable sur les dossiers


def test_semantic_search_only_on_indexes_with_embeddings():
    params = SearchParams(
        q="retraites", types=("amendements", "dossiers"), semantic_ratio=0.5
    )
    amendements, dossiers = build_request(params, SETTINGS)["queries"]
    assert amendements["hybrid"] == {"embedder": "hf-t4", "semanticRatio": 0.5}
    assert "hybrid" not in dossiers


def test_federated_request_weights_dossiers():
    params = SearchParams(
        q="retraites",
        types=("dossiers", "amendements"),
        mode="federated",
        page=3,
        limit=20,
    )
    request = build_request(params, SETTINGS)
    assert request["federation"] == {"limit": 20, "offset": 40}
    assert request["queries"][0]["federationOptions"] == {"weight": 1.5}
    assert "page" not in request["queries"][0]


def test_normalize_grouped_response_uses_type_names():
    raw = {
        "results": [
            {
                "indexUid": "amendements-2",
                "hits": [{"uid": "A1"}],
                "totalHits": 1,
                "facetDistribution": {"sort": {"Adopté": 1}},
            }
        ]
    }
    response = normalize_response(raw, SearchParams(), SETTINGS)
    assert response["results"]["amendements"] == {
        "hits": [{"uid": "A1"}],
        "total": 1,
        "facets": {"sort": {"Adopté": 1}},
    }


def test_normalize_federated_response_tags_each_hit():
    raw = {
        "hits": [{"uid": "D1", "_federation": {"indexUid": "dossiers"}}],
        "estimatedTotalHits": 1,
    }
    response = normalize_response(raw, SearchParams(mode="federated"), SETTINGS)
    assert response == {
        "mode": "federated",
        "hits": [{"type": "dossiers", "uid": "D1"}],
        "total": 1,
        "page": 1,
    }
