import pytest
from asyncpg import (
    CannotConnectNowError,
    InvalidCatalogNameError,
    InvalidPasswordError,
    PostgresConnectionError,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from backend.api.app.articles.adapter import list_articles
from backend.api.app.articles.schemas import Article
from backend.api.app.textes.adapter import list_texts
from backend.api.app.textes.schemas import Text

ROW = {
    "uid": "A1",
    "text_reference": "T1",
    "number": "1",
    "label": "Article premier",
    "content": "Texte",
    "position": 1,
    "chamber": "assemblee",
    "legislative_term": 17,
    "dossier_uid": None,
    "source_url": None,
}


async def test_adapter_query_and_mapping(db_session):
    reference = "T1' OR 1=1 --"
    db_session.execute.return_value.mappings.return_value.all.return_value = [ROW]
    articles = await list_articles(
        db_session, dossier_uid="D1", text_reference=reference, limit=3, offset=2
    )
    assert articles == [Article.model_validate(ROW)]
    db_session.execute.assert_awaited_once()
    statement = db_session.execute.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())
    assert list(statement.selected_columns.keys()) == list(ROW)
    for column, label in (
        ("id", "uid"),
        ("texte_ref", "text_reference"),
        ("numero", "number"),
        ("libelle", "label"),
        ("contenu", "content"),
        ("ordre", "position"),
        ("chambre", "chamber"),
        ("legislature", "legislative_term"),
        ("dossier_id", "dossier_uid"),
    ):
        assert f"textes_articles.{column} AS {label}" in sql
    assert "WHERE textes_articles.dossier_id = %(dossier_id_1)s" in sql
    assert "AND textes_articles.texte_ref = %(texte_ref_1)s" in sql
    assert "ORDER BY textes_articles.ordre, textes_articles.id" in sql
    assert "LIMIT %(param_1)s" in sql
    assert "OFFSET %(param_2)s" in sql
    assert compiled.params == {
        "dossier_id_1": "D1",
        "texte_ref_1": reference,
        "param_1": 3,
        "param_2": 2,
    }
    assert reference not in sql


TEXT = {
    "uid": "A1",
    "text_reference": "T1",
    "number": "1",
    "label": "Article premier",
    "content": "Texte",
    "position": 1,
    "chamber": "assemblee",
    "legislative_term": 17,
    "dossier_uid": "D1",
    "source_url": None,
}


@pytest.mark.parametrize("reference", [None, "T1' OR 1=1 --"])
async def test_texts_adapter_query_and_mapping(db_session, reference):
    dossier_uid = "D1' OR 1=1 --"
    db_session.execute.return_value.mappings.return_value.all.return_value = [TEXT]
    texts = await list_texts(
        db_session, dossier_uid=dossier_uid, text_reference=reference, limit=3, offset=2
    )
    assert texts == [Text.model_validate(TEXT)]
    db_session.execute.assert_awaited_once()
    statement = db_session.execute.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())
    assert list(statement.selected_columns.keys()) == list(Text.model_fields)
    for column, label in (
        ("id", "uid"),
        ("texte_ref", "text_reference"),
        ("numero", "number"),
        ("libelle", "label"),
        ("contenu", "content"),
        ("ordre", "position"),
        ("chambre", "chamber"),
        ("legislature", "legislative_term"),
        ("dossier_id", "dossier_uid"),
    ):
        assert f"textes_articles.{column} AS {label}" in sql
    assert "GROUP BY" not in sql
    assert "count(" not in sql
    assert "WHERE textes_articles.dossier_id = %(dossier_id_1)s" in sql
    params = {"dossier_id_1": dossier_uid, "param_1": 3, "param_2": 2}
    if reference is not None:
        assert "AND textes_articles.texte_ref = %(texte_ref_1)s" in sql
        params["texte_ref_1"] = reference
        assert reference not in sql
    assert "ORDER BY textes_articles.texte_ref, textes_articles.ordre, textes_articles.id" in sql
    assert compiled.params == params
    assert dossier_uid not in sql


@pytest.mark.parametrize(
    ("query", "rows", "limit", "offset", "has_more"),
    [
        ("&limit=1&offset=2", [TEXT, {**TEXT, "uid": "A2"}], 1, 2, True),
        ("&text_reference=T1&limit=1", [TEXT], 1, 0, False),
        ("", [], 20, 0, False),
        ("&limit=100&offset=10000", [], 100, 10000, False),
    ],
)
async def test_texts_page(client, db_session, query, rows, limit, offset, has_more):
    db_session.execute.return_value.mappings.return_value.all.return_value = rows
    response = await client.get(f"/api/v0/textes?dossier_uid=D1{query}")
    assert response.status_code == 200
    assert response.json() == {
        "items": rows[:limit],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }
    db_session.execute.assert_awaited_once()
    params = db_session.execute.call_args.args[0].compile().params
    assert params["dossier_id_1"] == "D1"
    assert (params["param_1"], params["param_2"]) == (limit + 1, offset)
    assert params.get("texte_ref_1") == ("T1" if "reference" in query else None)


@pytest.mark.parametrize(
    "query",
    [
        "",
        "limit=1",
        "dossier_uid=D1&limit=0",
        "dossier_uid=D1&limit=101",
        "dossier_uid=D1&limit=x",
        "dossier_uid=D1&offset=-1",
        "dossier_uid=D1&offset=10001",
    ],
)
async def test_texts_validation(client, db_session, query):
    response = await client.get("/api/v0/textes?" + query)
    assert response.status_code == response.json()["status"] == 422
    assert response.headers["content-type"] == "application/problem+json"
    db_session.execute.assert_not_awaited()


@pytest.mark.parametrize("path", ["/textes/T1", "/textes/T1/articles"])
async def test_removed_text_routes(client, db_session, path):
    response = await client.get("/api/v0" + path)
    assert response.status_code == 404
    db_session.execute.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (OperationalError("SELECT privé", {}, Exception("privé")), 503),
        (InterfaceError("SELECT privé", {}, Exception("privé")), 503),
        (PoolTimeoutError("privé"), 503),
        (OSError("privé"), 503),
        (TimeoutError("privé"), 503),
        (RuntimeError("privé"), 500),
        (PostgresConnectionError("privé"), 503),
        (InvalidPasswordError("privé"), 503),
        (InvalidCatalogNameError("privé"), 503),
        (CannotConnectNowError("privé"), 503),
    ],
)
async def test_database_errors_are_sanitized(client, db_session, error, status):
    db_session.execute.side_effect = error
    response = await client.get("/api/v0/textes?dossier_uid=D1")
    assert response.status_code == response.json()["status"] == status
    assert response.headers["content-type"] == "application/problem+json"
    assert "privé" not in response.text


async def test_articles_without_database(client):
    response = await client.get("/api/v0/textes?dossier_uid=D1")
    assert response.status_code == response.json()["status"] == 503
