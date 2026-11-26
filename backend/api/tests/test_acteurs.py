"""Hiérarchie des acteurs (organe > groupe politique > personne) sur la base synthétique."""

import pytest

API = "/api/v0"
ALPHA = {"uid": "PO2", "name": "Groupe Alpha", "short_name": "ALPHA", "color": "#112233"}
BETA = {"uid": "PO3", "name": "Groupe Bêta", "short_name": "BETA", "color": "#445566"}


async def get(client, path):
    response = await client.get(API + path)
    assert response.status_code == 200, response.json()
    return response.json()


async def uids(client, path):
    return [item["uid"] for item in (await get(client, path))["items"]]


async def test_organe_types_are_a_separate_reference(client, database):
    types = {item["code"]: item for item in await get(client, "/organes/types")}
    assert types["GP"] == {
        "code": "GP",
        "label": "Groupe politique",
        "family": "groupe",
        "chamber": None,
    }
    assert types["ASSEMBLEE"]["chamber"] == "assemblee"


async def test_organes_filter_by_type(client, database):
    assert len(await uids(client, "/organes")) == 5
    assert await uids(client, "/organes?type=COMPER") == ["PO4", "PO5"]
    sub = await get(client, "/organes/PO5")
    assert (sub["parent_uid"], sub["type_label"], sub["family"]) == (
        "PO4",
        "Commission permanente",
        "commission",
    )


async def test_groupes_are_organes(client, database):
    groupe = await get(client, "/groupes_politiques/PO2")
    assert (groupe["type"], groupe["chamber"], groupe["color"]) == ("GP", "assemblee", "#112233")
    assert groupe["political_position"] == "gauche"
    assert (await client.get(API + "/groupes_politiques/PO4")).status_code == 404


async def test_groupes_parent_organe_is_optional(client, database):
    assert await uids(client, "/groupes_politiques") == ["PO2", "PO3"]
    # Commission : seule Marie (Alpha) y siège.
    assert await uids(client, "/groupes_politiques?organe_uid=PO4") == ["PO2"]
    assert await uids(client, "/groupes_politiques?organe_uid=PO1") == ["PO2", "PO3"]
    assert await uids(client, "/groupes_politiques?organe_uid=inconnu") == []


async def test_personnes_need_organe(client, database):
    assert (await client.get(API + "/personnes")).status_code == 422
    assert (await client.get(API + "/personnes?groupe_uid=PO2")).status_code == 422


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("organe_uid=PO1", ["marie-dupont", "jean-martin"]),
        ("organe_uid=PO1&current=false", ["luc-ancien", "marie-dupont", "jean-martin"]),
        ("organe_uid=PO1&groupe_uid=PO2", ["marie-dupont"]),
        # Jean est passé d'Alpha à Bêta ; Luc a quitté l'AN et Alpha.
        (
            "organe_uid=PO1&groupe_uid=PO2&current=false",
            ["luc-ancien", "marie-dupont", "jean-martin"],
        ),
        ("organe_uid=PO1&groupe_uid=PO3", ["jean-martin"]),
        ("organe_uid=PO4", ["marie-dupont"]),
    ],
)
async def test_personnes_membership(client, database, query, expected):
    assert await uids(client, "/personnes?" + query) == expected


async def test_personne_shows_current_groupe(client, database):
    jean = await get(client, "/personnes/jean-martin")
    assert jean["groupe"] == BETA
    assert (await get(client, "/personnes/marie-dupont"))["groupe"] == ALPHA
    assert (await get(client, "/personnes/luc-ancien"))["groupe"] is None
    assert (await client.get(API + "/personnes/inconnu")).status_code == 404
