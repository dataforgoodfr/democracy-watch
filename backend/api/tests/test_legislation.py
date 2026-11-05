from datetime import datetime
from urllib.parse import urlencode

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from backend.api.app.amendements.schemas import Amendement
from backend.api.app.dossiers.schemas import Dossier

SUBMITTED_AT = datetime(2026, 1, 2, 10, 30)
ADOPTED_AT = datetime(2026, 2, 3, 14, 45)
UPDATED_AT = datetime(2026, 3, 4, 8, 15)
AMENDEMENT = {
    "uid": "db-amendement",
    "source_uid": "source-amendement",
    "number": "42",
    "chamber": "assemblee",
    "legislative_term": 17,
    "targeted_article": "Article premier",
    "body": "Dispositif",
    "explanation": "Exposé sommaire",
    "outcome": "Adopté",
    "submitted_at": SUBMITTED_AT,
    "author": "Auteur",
    "text_reference": "texte-reference",
    "dossier_uid": "db-dossier",
    "parliamentarian_uid": "db-parliamentarian",
    "group_reference": "groupe-reference",
    "author_reference": "auteur-reference",
    "paragraph": "Alinéa 3",
    "paragraph_number": 3,
    "order_number": 7,
    "parent_amendement_uid": "db-amendement-parent",
    "sitting_reference": "seance-reference",
    "joint_discussion_id": "discussion-commune",
    "identical_discussion_id": "discussion-identique",
}
DOSSIER = {
    "uid": "db-dossier",
    "source_uid": "source-dossier",
    "title": "Projet de loi",
    "legislative_term": 17,
    "status": "Adopté",
    "procedure": "Procédure accélérée",
    "submitted_at": SUBMITTED_AT,
    "adopted_at": ADOPTED_AT,
    "assembly_url": "https://example.org/assemblee",
    "senate_url": "https://example.org/senat",
    "legifrance_url": "https://example.org/legifrance",
    "law_number": "2026-123",
    "law_title": "Loi n° 2026-123",
    "law_published_at": ADOPTED_AT,
    "subject_uid": "db-subject",
    "updated_at": UPDATED_AT,
}


# Filtres obligatoires par collection, avec les paramètres SQL attendus.
REQUIRED_FILTERS = {
    "amendements": (
        {"dossier_uid": "D1", "text_reference": "T1"},
        {"dossier_id_1": "D1", "texte_ref_1": "T1"},
    ),
    "dossiers": ({}, {}),
}


@pytest.fixture(params=[("amendements", Amendement, AMENDEMENT), ("dossiers", Dossier, DOSSIER)])
def legislation(request):
    return request.param


def assert_projection(statement, model):
    columns = statement.selected_columns
    assert list(columns.keys()) == list(model.model_fields)
    assert columns.uid.element.primary_key
    assert not columns.source_uid.element.primary_key
    assert columns.source_uid.element.name == columns.uid.name
    assert "source_data" not in str(statement)
    for name in ("dossier_uid", "parliamentarian_uid", "parent_amendement_uid", "subject_uid"):
        if name in columns:
            foreign_keys = columns[name].element.foreign_keys
            assert len(foreign_keys) == 1
            assert next(iter(foreign_keys)).column.primary_key


@pytest.mark.parametrize("nullable", [False, True])
async def test_detail_mapping_and_primary_key_binding(client, db_session, legislation, nullable):
    resource, model, row = legislation
    if nullable:
        row = {
            name: None if type(None) in getattr(field.annotation, "__args__", ()) else row[name]
            for name, field in model.model_fields.items()
        }
    db_session.execute.return_value.mappings.return_value.one_or_none.return_value = row
    uid = "db-key' OR 1=1 --"
    response = await client.get(f"/api/v0/{resource}/{uid}")
    assert response.status_code == 200
    expected = {
        name: value.isoformat() if isinstance(value, datetime) else value
        for name, value in row.items()
    }
    assert response.json() == expected
    assert expected["uid"] != expected["source_uid"]
    db_session.execute.assert_awaited_once()
    statement = db_session.execute.call_args.args[0]
    assert_projection(statement, model)
    compiled = statement.compile(dialect=postgresql.dialect())
    assert compiled.params == {"id_1": uid}
    assert uid not in str(compiled)
    assert statement.whereclause.left is statement.selected_columns.uid.element
    assert f"WHERE {statement.whereclause.left} = %(id_1)s" in str(compiled)
    db_session.execute.return_value.mappings.return_value.one_or_none.assert_called_once_with()


@pytest.mark.parametrize(
    ("query", "count", "limit", "offset", "has_more"),
    [
        ("?limit=1&offset=2", 2, 1, 2, True),
        ("?limit=1", 1, 1, 0, False),
        ("", 0, 20, 0, False),
        ("?limit=100&offset=10000", 0, 100, 10000, False),
    ],
)
async def test_collection_pagination(
    client, db_session, legislation, query, count, limit, offset, has_more
):
    resource, model, row = legislation
    rows = [{**row, "uid": f"db-{index}"} for index in range(count)]
    db_session.execute.return_value.mappings.return_value.all.return_value = rows
    filters, filter_params = REQUIRED_FILTERS[resource]
    separator = "&" if query else "?"
    url = f"/api/v0/{resource}{query}" + (separator + urlencode(filters) if filters else "")
    response = await client.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "items": [model.model_validate(item).model_dump(mode="json") for item in rows[:limit]],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }
    db_session.execute.assert_awaited_once()
    statement = db_session.execute.call_args.args[0]
    assert_projection(statement, model)
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())
    assert compiled.params == {**filter_params, "param_1": limit + 1, "param_2": offset}
    primary_key = statement.selected_columns.uid.element
    assert f"ORDER BY {primary_key}" in sql
    assert "LIMIT %(param_1)s" in sql
    assert "OFFSET %(param_2)s" in sql
    assert ("WHERE" in sql) is bool(filters)
    db_session.execute.return_value.mappings.return_value.all.assert_called_once_with()


async def test_missing_detail(client, db_session, legislation):
    resource, _, _ = legislation
    db_session.execute.return_value.mappings.return_value.one_or_none.return_value = None
    response = await client.get(f"/api/v0/{resource}/unknown")
    assert response.status_code == response.json()["status"] == 404
    assert "introuvable" in response.json()["detail"]
    db_session.execute.assert_awaited_once()


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "offset=10001"])
async def test_pagination_bounds(client, db_session, legislation, query):
    resource, _, _ = legislation
    response = await client.get(f"/api/v0/{resource}?{query}")
    assert response.status_code == 422
    db_session.execute.assert_not_awaited()


def test_nullable_fields_are_required(legislation):
    _, model, row = legislation
    assert all(field.is_required() for field in model.model_fields.values())
    with pytest.raises(ValidationError):
        model.model_validate(
            {name: row[name] for name in ("uid", "source_uid", "legislative_term")}
        )


@pytest.mark.parametrize(
    ("params", "clauses"),
    [
        (
            {},
            [
                "amendements.dossier_id = %(dossier_id_1)s",
                "amendements.texte_ref = %(texte_ref_1)s",
            ],
        ),
        (
            {"article_uid": "A1"},
            [
                "(amendements.texte_ref, upper(regexp_replace(amendements.article_vise,",
                "IN (SELECT textes_articles.texte_ref, textes_articles.numero FROM textes_articles"
                " WHERE textes_articles.id = %(id_1)s",
            ],
        ),
    ],
)
async def test_amendements_filtered_by_hierarchy(client, db_session, params, clauses):
    params = {**REQUIRED_FILTERS["amendements"][0], **params}
    response = await client.get("/api/v0/amendements", params=params)
    assert response.status_code == 200
    compiled = db_session.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    assert set(params.values()) <= set(compiled.params.values())
    sql = " ".join(str(compiled).split())
    assert all(clause in sql for clause in clauses)


@pytest.mark.parametrize("query", ["", "dossier_uid=D1", "text_reference=T1&article_uid=A1"])
async def test_amendements_require_dossier_and_text(client, db_session, query):
    response = await client.get(f"/api/v0/amendements?{query}")
    assert response.status_code == 422
    db_session.execute.assert_not_awaited()
