"""Hiérarchie législative (dossier > texte > article > amendement) sur la base synthétique."""

import pytest

API = "/api/v0"
DOSSIER = {
    "uid": "DLR5L17N1",
    "title": "Projet de loi de finances pour 2026",
    "short_title": "PLF 2026",
}
TEXTE = {"uid": "PRJLANR5L17B0001", "nature": "projet", "number": 1}


async def items(client, path):
    response = await client.get(API + path)
    assert response.status_code == 200, response.json()
    return response.json()["items"]


async def test_dossiers_most_recent_first_with_loi(client, database):
    dossiers = await items(client, "/dossiers")
    assert [dossier["uid"] for dossier in dossiers] == ["DLR5L17N1", "DLR5L17N2"]
    assert dossiers[0]["procedure_label"] == "Loi de finances de l'année"
    assert dossiers[0]["loi"] is None
    assert dossiers[1]["outcome"] == "promulgue"
    assert dossiers[1]["loi"] == {
        "number": "2025-12",
        "title": "Loi relative aux essais",
        "published_on": "2025-03-05",
        "legifrance_url": "https://www.legifrance.gouv.fr/jorf/id/TEST",
    }


async def test_textes_parent_is_optional(client, database):
    assert len(await items(client, "/textes")) == 3
    textes = await items(client, "/textes?dossier_uid=DLR5L17N1")
    assert [texte["uid"] for texte in textes] == ["PRJLANR5L17B0001", "PRJLANR5L17BTC0002"]
    assert textes[0]["dossier"] == DOSSIER
    assert (textes[0]["term"], textes[0]["position"]) == (17, 1)
    assert await items(client, "/textes?dossier_uid=inconnu") == []


async def test_articles_need_dossier_and_accept_texte(client, database):
    assert (await client.get(API + "/articles")).status_code == 422
    articles = await items(client, "/articles?dossier_uid=DLR5L17N1")
    assert [article["uid"] for article in articles] == [
        "PRJLANR5L17B0001-10",
        "PRJLANR5L17B0001-15",
        "PRJLANR5L17B0001-20",
        "PRJLANR5L17BTC0002-10",
    ]
    placeholder = articles[1]
    assert placeholder["is_placeholder"] and placeholder["number"] is None
    assert placeholder["texte"] == TEXTE and placeholder["dossier"] == DOSSIER
    filtered = await items(client, "/articles?dossier_uid=DLR5L17N1&texte_uid=PRJLANR5L17BTC0002")
    assert [article["uid"] for article in filtered] == ["PRJLANR5L17BTC0002-10"]
    # Texte d'un autre dossier : collection vide.
    assert await items(client, "/articles?dossier_uid=DLR5L17N2&texte_uid=PRJLANR5L17B0001") == []


async def test_amendements_need_dossier_and_texte(client, database):
    for query in ("", "?dossier_uid=DLR5L17N1", "?texte_uid=PRJLANR5L17B0001"):
        assert (await client.get(API + "/amendements" + query)).status_code == 422
    base = "/amendements?dossier_uid=DLR5L17N1&texte_uid=PRJLANR5L17B0001"
    amendements = await items(client, base)
    assert [item["number"] for item in amendements] == ["1", "2", "3"]
    first, _, sub = amendements
    assert first["dossier"] == DOSSIER and first["texte"] == TEXTE
    assert first["article"] == {
        "uid": "PRJLANR5L17B0001-10",
        "number": "PREMIER",
        "label": "Article premier",
    }
    assert first["author"] == {"uid": "marie-dupont", "first_name": "Marie", "last_name": "Dupont"}
    assert first["groupe"] == {
        "uid": "PO2",
        "name": "Groupe Alpha",
        "short_name": "ALPHA",
        "color": "#112233",
    }
    assert first["examining_organe"]["uid"] == "PO1"
    assert (first["status"], first["outcome"]) == ("traite", "rejete")
    assert sub["parent_uid"] == first["uid"]
    assert sub["article"] is sub["author"] is sub["groupe"] is None
    targeted = await items(client, base + "&article_uid=PRJLANR5L17B0001-15")
    assert [item["number"] for item in targeted] == ["2"]
    assert await items(client, base.replace("DLR5L17N1", "DLR5L17N2")) == []


async def test_pagination_has_more(client, database):
    response = await client.get(API + "/textes?limit=2&offset=0")
    page = response.json()
    assert (len(page["items"]), page["has_more"]) == (2, True)
    page = (await client.get(API + "/textes?limit=2&offset=2")).json()
    assert (len(page["items"]), page["has_more"]) == (1, False)


@pytest.mark.parametrize(
    ("path", "uid"),
    [
        ("/dossiers/DLR5L17N2", "DLR5L17N2"),
        ("/textes/PRJLANR5L17BTC0002", "PRJLANR5L17BTC0002"),
        ("/articles/PRJLANR5L17B0001-20", "PRJLANR5L17B0001-20"),
        ("/amendements/AMANR5L17PO1B0001P0D1N000002", "AMANR5L17PO1B0001P0D1N000002"),
    ],
)
async def test_get_one(client, database, path, uid):
    response = await client.get(API + path)
    assert response.status_code == 200
    assert response.json()["uid"] == uid
    missing = await client.get(API + path.rsplit("/", 1)[0] + "/inconnu")
    assert missing.status_code == 404
    assert missing.headers["content-type"] == "application/problem+json"
