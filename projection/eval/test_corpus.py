"""Construction du corpus depuis Tricoteuses, sans réseau.

L'adaptateur est remplacé par monkeypatch.
"""

import dataclasses
from collections import Counter

import pytest

from projection.datasources import tricoteuses
from projection.eval import corpus

ARTICLES = (tricoteuses.Article("PREMIER", ("Le premier alinéa.",)),)


def amendement(uid, sort):
    return tricoteuses.Amendement(
        uid=uid,
        numero=uid,
        texte_ref="B1",
        article_vise="ART. PREMIER",
        alinea=None,
        dispositif="<p>Rédiger.</p>",
        parent_uid=None,
        tri_amendement="a",
        date_sort=None,
        sort=sort,
        auteur="M. Untel",
        numero_ordre=1,
    )


@pytest.fixture
def api(monkeypatch, tmp_path):
    """Remplace `read_text` et `text_amendements` de l'adaptateur Tricoteuses (aucun accès réseau).

    Références fictives : B1 (texte déposé) et BTC1 (texte de commission) renvoient `ARTICLES`
    et un amendement adopté construit par `amendement()` ; BTA1 (texte adopté) lève
    TextNotFound. Le cache disque de `corpus` est redirigé vers `tmp_path`. Renvoie le nombre
    d'appels à `read_text` par référence, pour vérifier le cache.
    """
    monkeypatch.setattr(corpus, "CACHE", tmp_path)
    calls = Counter()

    def read_text(ref):
        calls[ref] += 1
        if ref == "BTA1":
            raise tricoteuses.TextNotFound(ref)
        return tricoteuses.Text(ref, f"Texte {ref}", ARTICLES)

    monkeypatch.setattr(tricoteuses, "read_text", read_text)
    monkeypatch.setattr(
        tricoteuses,
        "text_amendements",
        lambda ref: {
            "B1": [amendement("AM1", "Adopté")],
            "BTC1": [amendement("AM2", "Adopté")],
        }.get(ref, []),
    )
    return calls


def test_dossier_steps(api):
    excluded = Counter()
    lecture = tricoteuses.PremiereLecture("DL1", depose="B1", commission="BTC1", adopte="BTA1")
    steps = corpus.dossier_steps(lecture, excluded)
    assert [e["id"] for e in steps] == ["DL1:commission"]
    assert excluded == {"texte de sortie introuvable": 1}
    step = steps[0]
    assert step["titre"] == "Texte B1" and step["sortie"]["ref"] == "BTC1"
    assert "auteur" not in step["amendements"][0]
    # Le format se relit en objets de l'adaptateur (celui que run.py lira).
    assert [tricoteuses.Amendement(**a, auteur=None).uid for a in step["amendements"]] == ["AM1"]
    assert [tricoteuses.Article(**a).numero for a in step["entree"]["articles"]] == ["PREMIER"]


def test_missing_act_and_cache(api):
    excluded = Counter()
    assert corpus.dossier_steps(tricoteuses.PremiereLecture("DL2", depose="B1"), excluded) == []
    assert excluded == {"acte manquant": 2}
    corpus.text("B1")
    corpus.text("B1")
    assert api["B1"] == 1


def test_corpus_fields():
    expected_items = {f.name for f in dataclasses.fields(tricoteuses.Amendement)} - {"auteur"}
    assert set(corpus.FIELDS) == expected_items


def test_resolve():
    previous = [
        {"numero": "1", "lignes": ["Texte."], "supprime": False, "inchange": False},
        {"numero": "2", "lignes": [], "supprime": True, "inchange": False},
    ]
    articles = [
        {"numero": n, "lignes": [], "supprime": False, "inchange": True} for n in ("1", "2", "3")
    ]
    resolved = corpus.resolve(articles, previous)
    # « (Conforme) » après une suppression en commission : l'article reste supprimé.
    assert [(a["lignes"], a["supprime"]) for a in resolved] == [
        (["Texte."], False),
        ([], True),
        ([], False),
    ]
    assert corpus.resolve(articles, None) == articles


def test_seance_unchanged_from_depose(api, monkeypatch):
    """En séance, un article inchangé en commission puis en séance reprend le texte déposé."""
    unchanged = (tricoteuses.Article("PREMIER", (), inchange=True),)
    monkeypatch.setattr(
        tricoteuses,
        "read_text",
        lambda ref: tricoteuses.Text(ref, f"Texte {ref}", ARTICLES if ref == "B1" else unchanged),
    )
    lecture = tricoteuses.PremiereLecture("DL1", depose="B1", commission="BTC1", adopte="BTA1")
    steps = corpus.dossier_steps(lecture, Counter())
    assert [s["etape"] for s in steps] == ["commission", "seance"]
    for step in steps:
        assert (
            list(step["entree"]["articles"][0]["lignes"])
            == list(step["sortie"]["articles"][0]["lignes"])
            == ["Le premier alinéa."]
        )
