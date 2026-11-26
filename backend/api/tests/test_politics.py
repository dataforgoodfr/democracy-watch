"""Contrats publics et requêtes politiques, sans accès à un service externe."""

from datetime import datetime

import pytest
from sqlalchemy.dialects import postgresql

from backend.api.app.declarations_hatvp import adapter as declarations
from backend.api.app.declarations_hatvp.schemas import HatvpDeclaration
from backend.api.app.groupes_politiques import adapter as groups
from backend.api.app.groupes_politiques.schemas import PoliticalGroup
from backend.api.app.parlementaires import adapter as parliamentarians
from backend.api.app.parlementaires.schemas import Parliamentarian


@pytest.fixture(
    params=[
        (
            "parlementaires",
            parliamentarians.list_parliamentarians,
            parliamentarians.get_parliamentarian,
            Parliamentarian,
            {
                "uid": "P1",
                "slug": "alice-martin",
                "first_name": "Alice",
                "last_name": "Martin",
                "chamber": "assemblee",
                "active": True,
                "group_uid": "G1",
                "constituency_uid": "C1",
                "photo_url": "https://example.org/photo",
                "website": "https://example.org",
            },
            "Parlementaire introuvable",
        ),
        (
            "groupes_politiques",
            groups.list_political_groups,
            groups.get_political_group,
            PoliticalGroup,
            {
                "uid": "G1",
                "slug": "groupe",
                "name": "Groupe",
                "chamber": "senat",
                "active": False,
                "full_name": "Groupe politique",
                "short_name": "GP",
                "color": "#123456",
                "political_position": "centre",
                "legislative_term": 17,
                "active_member_count": 0,
            },
            "Groupe politique introuvable",
        ),
        (
            "declarations_hatvp",
            declarations.list_hatvp_declarations,
            declarations.get_hatvp_declaration,
            HatvpDeclaration,
            {
                "uid": "D1",
                "parliamentarian_uid": "P1",
                "document_type": "interets",
                "submitted_at": datetime(2025, 1, 2, 12, 30),
                "published_at": datetime(2025, 2, 3),
                "status": "publie",
                "dossier_url": "https://example.org/dossier",
            },
            "Déclaration HATVP introuvable",
        ),
    ],
    ids=["parliamentarians", "groups", "declarations"],
)
def case(request):
    return request.param


async def test_adapter_projection_and_order(db_session, case):
    _, list_items, _, model, row, _ = case
    db_session.execute.return_value.mappings.return_value.all.return_value = [row]
    items = await list_items(db_session, limit=3, offset=2)
    assert items == [model.model_validate(row)]
    db_session.execute.assert_awaited_once()
    statement = db_session.execute.call_args.args[0]
    columns = statement.selected_columns
    assert list(columns.keys()) == list(row) == list(model.model_fields)
    primary_key = next(iter(columns.uid.element.table.primary_key))
    assert columns.uid.element is primary_key
    for field in ("parliamentarian_uid", "group_uid", "constituency_uid"):
        if field in columns:
            assert columns[field].element.foreign_keys
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())
    assert f"ORDER BY {primary_key.table.name}.{primary_key.name}" in sql
    assert "LIMIT %(param_1)s" in sql
    assert "OFFSET %(param_2)s" in sql
    assert compiled.params == {"param_1": 3, "param_2": 2}
    assert statement.whereclause is None


@pytest.mark.parametrize("found", [True, False])
async def test_adapter_detail_bound_primary_key(db_session, case, found):
    _, _, get_item, model, row, _ = case
    uid = "primary-key' OR 1=1 --"
    result = db_session.execute.return_value.mappings.return_value
    result.one_or_none.return_value = row if found else None
    item = await get_item(db_session, uid)
    assert item == (model.model_validate(row) if found else None)
    db_session.execute.assert_awaited_once()
    result.one_or_none.assert_called_once_with()
    statement = db_session.execute.call_args.args[0]
    primary_key = next(iter(statement.selected_columns.uid.element.table.primary_key))
    assert statement.whereclause.left is primary_key
    compiled = statement.compile(dialect=postgresql.dialect())
    assert list(compiled.params.values()) == [uid]
    assert uid not in str(compiled)
    assert f"WHERE {primary_key.table.name}.{primary_key.name} = %(" in str(compiled)


@pytest.mark.parametrize("nullable", [False, True])
@pytest.mark.parametrize("detail", [False, True])
async def test_public_mapping(client, db_session, case, nullable, detail):
    path, _, _, model, row, _ = case
    row = {
        key: None if nullable and not model.model_fields[key].is_required() else value
        for key, value in row.items()
    }
    expected = {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in row.items()
    }
    result = db_session.execute.return_value.mappings.return_value
    result.all.return_value = [{**row, "private_payload": "secret"}]
    result.one_or_none.return_value = {**row, "private_payload": "secret"}
    response = await client.get(f"/api/v0/{path}" + (f"/{row['uid']}" if detail else ""))
    assert response.status_code == 200
    assert (response.json() if detail else response.json()["items"][0]) == expected
    assert "secret" not in response.text
    db_session.execute.assert_awaited_once()


@pytest.mark.parametrize(
    ("count", "limit", "offset", "has_more"),
    [
        (2, 1, 2, True),
        (1, 1, 0, False),
        (0, 20, 0, False),
        (0, 100, 10000, False),
    ],
)
async def test_pagination(client, db_session, case, count, limit, offset, has_more):
    path, _, _, model, row, _ = case
    rows = [{**row, "uid": f"item-{index}"} for index in range(count)]
    db_session.execute.return_value.mappings.return_value.all.return_value = rows
    response = await client.get(f"/api/v0/{path}?limit={limit}&offset={offset}")
    assert response.status_code == 200
    assert response.json() == {
        "items": [model.model_validate(item).model_dump(mode="json") for item in rows[:limit]],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }
    db_session.execute.assert_awaited_once()
    assert db_session.execute.call_args.args[0].compile().params == {
        "param_1": limit + 1,
        "param_2": offset,
    }


async def test_detail_not_found(client, db_session, case):
    path, _, _, _, _, message = case
    db_session.execute.return_value.mappings.return_value.one_or_none.return_value = None
    response = await client.get(f"/api/v0/{path}/unknown")
    assert response.status_code == 404
    assert response.json()["detail"] == message
    db_session.execute.assert_awaited_once()


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=x", "offset=-1", "offset=10001"])
async def test_invalid_pagination(client, db_session, case, query):
    response = await client.get(f"/api/v0/{case[0]}?{query}")
    assert response.status_code == 422
    db_session.execute.assert_not_awaited()
