import pytest
from sqlalchemy.dialects import postgresql

ARTICLE = {
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


@pytest.mark.parametrize("reference", [None, "T1"])
async def test_articles_collection(client, db_session, reference):
    rows = [ARTICLE, {**ARTICLE, "uid": "A2"}]
    db_session.execute.return_value.mappings.return_value.all.return_value = rows
    params: dict[str, str | int] = {"dossier_uid": "D1", "limit": 1, "offset": 2}
    if reference is not None:
        params["text_reference"] = reference
    response = await client.get("/api/v0/articles", params=params)
    assert response.status_code == 200
    assert response.json() == {"items": [ARTICLE], "limit": 1, "offset": 2, "has_more": True}
    statement = db_session.execute.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert compiled.params == (
        {"dossier_id_1": "D1", "param_1": 2, "param_2": 2}
        if reference is None
        else {
            "dossier_id_1": "D1",
            "texte_ref_1": reference,
            "param_1": 2,
            "param_2": 2,
        }
    )
    sql = " ".join(str(compiled).split())
    order = "textes_articles.ordre, textes_articles.id"
    if reference is None:
        order = "textes_articles.texte_ref, " + order
    assert "ORDER BY " + order in sql
    assert ("textes_articles.texte_ref = " in sql) is (reference is not None)


@pytest.mark.parametrize("found", [True, False])
async def test_article_detail(client, db_session, found):
    db_session.execute.return_value.mappings.return_value.one_or_none.return_value = (
        ARTICLE if found else None
    )
    uid = "primary-key' OR 1=1 --"
    response = await client.get(f"/api/v0/articles/{uid}")
    assert response.status_code == (200 if found else 404)
    if found:
        assert response.json() == ARTICLE
    else:
        assert response.json()["status"] == 404
    db_session.execute.assert_awaited_once()
    statement = db_session.execute.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert compiled.params == {"id_1": uid}
    assert uid not in str(compiled)
    assert statement.whereclause.left is statement.selected_columns.uid.element


async def test_empty_collection(client, db_session):
    response = await client.get("/api/v0/articles?dossier_uid=D1")
    assert response.status_code == 200
    assert response.json() == {"items": [], "limit": 20, "offset": 0, "has_more": False}


@pytest.mark.parametrize(
    "query",
    [
        "text_reference=T1",
        "dossier_uid=D1&limit=0",
        "dossier_uid=D1&limit=101",
        "dossier_uid=D1&offset=-1",
        "dossier_uid=D1&offset=10001",
    ],
)
async def test_pagination_bounds(client, db_session, query):
    response = await client.get(f"/api/v0/articles?{query}")
    assert response.status_code == 422
    db_session.execute.assert_not_awaited()


async def test_articles_filtered_by_dossier(client, db_session):
    response = await client.get(
        "/api/v0/articles", params={"dossier_uid": "D1", "text_reference": "T1"}
    )
    assert response.status_code == 200
    compiled = db_session.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    assert compiled.params == {
        "dossier_id_1": "D1",
        "texte_ref_1": "T1",
        "param_1": 21,
        "param_2": 0,
    }
    sql = " ".join(str(compiled).split())
    assert "textes_articles.dossier_id = %(dossier_id_1)s" in sql
    assert "textes_articles.texte_ref = %(texte_ref_1)s" in sql
