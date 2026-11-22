"""Tests de l'adaptateur Tricoteuses, sans réseau (get remplacé par monkeypatch)."""

from typing import Any

import pytest

from datasources import tricoteuses

DOCUMENT: dict[str, Any] = {
    "uid": "PIONTEST",
    "titrePrincipal": "Proposition de loi de test",
    "subdivisions": [
        {"type": "Article", "hash": "h2", "titre": "Article 2 (Supprimé)", "sequence": 2},
        {"type": "Exposé des motifs", "hash": "hx", "titre": "EXPOSÉ DES MOTIFS", "sequence": 0},
        {"type": "Article", "hash": "h1", "titre": "Article 1er (nouveau)", "sequence": 1},
    ],
    "alineas": [
        {"articleRefHash": "h1", "numero": 2, "texte": "Le second alinéa."},
        {"articleRefHash": "h1", "numero": 0, "texte": "(Non modifié)"},
        {"articleRefHash": "h1", "numero": 1, "texte": "Le premier alinéa."},
        {"articleRefHash": "hx", "numero": 0, "texte": "Mesdames, Messieurs,"},
    ],
}
AMENDEMENT = {
    "uid": "AM1",
    "numeroLong": "CE1",
    "documentRefUid": "PIONTEST",
    "divisionArticleDesignationCourte": "ART. PREMIER",
    "alineaDesignation": "Alinéa 2",
    "dispositifHtml": "<p>À l’alinéa 2, substituer au mot :</p><p>« second »</p>"
    "<p>le mot :</p><p>« dernier ».</p>",
    "amendementParentRefUid": None,
    "triAmendement": "a",
    "dateSort": "2025-02-19T14:21:18.000Z",
    "sortAmendement": "Adopté",
    "idDiscussionIdentique": None,
    "signatairesLibelle": "Mme Barth&#232;s",
}
DELETION = dict(
    AMENDEMENT,
    uid="AM3",
    numeroLong="CE3",
    dispositifHtml="<p>Supprimer l’alinéa 1.</p>",
    dateSort="2025-02-19T15:00:00.000Z",
)


class Response:
    def __init__(self, data, pages=1):
        self.data, self.headers = data, {"total-page": str(pages)}

    def json(self):
        return {"data": self.data}


@pytest.fixture
def api(monkeypatch):
    """Remplace l'API : le document de test, et ses amendements sur deux pages."""
    calls = []

    def get(path, params):
        calls.append((path, params))
        if path == "/documents/PIONTEST":
            assert params == {"include": "subdivisions,alineas"}
            return Response(DOCUMENT)
        if path.startswith("/documents/"):
            raise tricoteuses.TextNotFound(path)
        if path == "/amendements/json":
            removed = dict(AMENDEMENT, uid="AM2", sortAmendement="Retiré")
            page = [AMENDEMENT, DELETION] if params["page"] == 1 else [removed]
            return Response(page, pages=2)
        raise AssertionError(path)

    monkeypatch.setattr(tricoteuses, "get", get)
    return calls


def test_numbers_from_title():
    assert tricoteuses.numbers_from_title("Article 1er") == ["PREMIER"]
    assert tricoteuses.numbers_from_title("Article unique") == ["UNIQUE"]
    assert tricoteuses.numbers_from_title("Article 5 bis (nouveau)") == ["5 BIS"]
    assert tricoteuses.numbers_from_title("Articles 12") == ["12"]
    assert tricoteuses.numbers_from_title("Articles 2 à 4 (Supprimés)") == ["2", "3", "4"]
    assert tricoteuses.numbers_from_title("Articles 8 ter et 8 quater") == ["8 TER", "8 QUATER"]
    assert tricoteuses.numbers_from_title("Articles 15, 16 à 18 et 20") == [
        "15",
        "16",
        "17",
        "18",
        "20",
    ]
    # Espaces manquants dans le titre.
    assert tricoteuses.numbers_from_title("Articles 4 nonies et4 decies") == [
        "4 NONIES",
        "4 DECIES",
    ]
    assert tricoteuses.numbers_from_title("Article 1erbis") == ["1ER BIS"]
    assert tricoteuses.numbers_from_title("Article 25C") == ["25 C"]


def test_amendement_from():
    amendement = tricoteuses.amendement_from(dict(AMENDEMENT, idDiscussionIdentique=42))
    assert amendement.article_vise == "ART. PREMIER"
    assert amendement.dispositif.startswith("<p>")
    assert amendement.date_sort == "2025-02-19T14:21:18"
    assert amendement.id_identique == "42"
    assert amendement.auteur == "Mme Barthès"


def test_amendements_reads_all_pages(api):
    amendements = tricoteuses.text_amendements("PIONTEST")
    assert [a.uid for a in amendements] == ["AM1", "AM3", "AM2"]
    assert [p["page"] for c, p in api if c == "/amendements/json"] == [1, 2]


def test_deposit_order_number():
    assert tricoteuses.amendement_from(dict(AMENDEMENT, numeroOrdreDepot="393")).numero_ordre == 393
    assert tricoteuses.amendement_from(dict(AMENDEMENT, numeroOrdreDepot=393)).numero_ordre == 393
    assert tricoteuses.amendement_from(AMENDEMENT).numero_ordre is None


def test_articles_from_document():
    articles = tricoteuses.articles_from_document(DOCUMENT)
    assert articles == (
        tricoteuses.Article("PREMIER", ("Le premier alinéa.", "Le second alinéa.")),
        tricoteuses.Article("2", (), supprime=True),
    )


def test_read_text(api):
    text = tricoteuses.read_text("PIONTEST")
    assert (text.uid, text.titre) == ("PIONTEST", "Proposition de loi de test")
    assert [a.numero for a in text.articles] == ["PREMIER", "2"]


def test_flattened_table_stays_one_alinea():
    table = {
        "articleRefHash": "h1",
        "numero": 3,
        "texte": "«\tPopulation\tTaux\t\t\n\tMoins de 500\t28,1\t\t\n",
    }
    articles = tricoteuses.articles_from_document(
        dict(DOCUMENT, alineas=DOCUMENT["alineas"] + [table])
    )
    assert articles[0].lignes[-1] == "« Population Taux Moins de 500 28,1"


def test_premiere_lecture_texts(monkeypatch):
    acts = {
        "AN1-DEPOT": [{"dossierRefUid": "DL1", "texteAssocieRefUid": "PIONB1"}],
        "AN1-COM-FOND-RAPPORT": [
            {"dossierRefUid": "DL1", "texteAdopteRefUid": "PIONBTC1"},
            {"dossierRefUid": "DL2", "texteAdopteRefUid": None},
        ],
        # La décision en séance peut viser un TAP : seul le BTA est le texte adopté.
        "AN1-DEBATS-DEC": [
            {"dossierRefUid": "DL1", "texteAssocieRefUid": "PIONTAP1"},
            {"dossierRefUid": "DL1", "texteAssocieRefUid": "PIONBTA1"},
        ],
    }

    def get(path, params):
        assert path == "/actesLegislatifs/json" and params["legislature"] == 17
        return Response(acts[params["codeActe"]])

    monkeypatch.setattr(tricoteuses, "get", get)
    assert tricoteuses.premiere_lecture_texts(17) == [
        tricoteuses.PremiereLecture(
            "DL1", depose="PIONB1", commission="PIONBTC1", adopte="PIONBTA1"
        )
    ]


def test_unchanged_article_and_false_article():
    subdivisions = DOCUMENT["subdivisions"] + [
        {"type": "Article", "hash": "h3", "titre": "Article 3", "sequence": 3},
        {"type": "Article", "hash": "h4", "titre": "Article 4", "sequence": 4},
        # Tableau de dispositions applicables outre-mer, typé « Article » par Tricoteuses.
        {"type": "Article", "hash": "ht", "titre": "ARTICLES APPLICABLES L. 623-4", "sequence": 5},
    ]
    alineas = DOCUMENT["alineas"] + [
        {"articleRefHash": "h3", "numero": 0, "texte": "(Conforme)"},
        {"articleRefHash": "h4", "numero": 0, "texte": "(Suppression conforme)"},
        {"articleRefHash": "ht", "numero": 0, "texte": "L. 623-4"},
    ]
    articles = tricoteuses.articles_from_document(
        dict(DOCUMENT, subdivisions=subdivisions, alineas=alineas)
    )
    assert articles[2:] == (
        tricoteuses.Article("3", (), inchange=True),
        tricoteuses.Article("4", (), supprime=True),
    )
    # « (Non modifié) » suivi du texte : l'article a ses lignes, il n'est pas marqué inchangé.
    assert not articles[0].inchange


def test_article_from_range_is_flagged():
    subdivisions = [{"type": "Article", "hash": "h", "titre": "Articles 2 à 3", "sequence": 1}]
    alineas = [{"articleRefHash": "h", "numero": 1, "texte": "Texte partagé."}]
    articles = tricoteuses.articles_from_document(
        {"uid": "T", "subdivisions": subdivisions, "alineas": alineas}
    )
    assert [(a.numero, a.issu_de_plage) for a in articles] == [("2", True), ("3", True)]
    assert not tricoteuses.articles_from_document(DOCUMENT)[0].issu_de_plage
