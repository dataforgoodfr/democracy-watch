"""Métriques de l'évaluation, sur des articles écrits à la main."""

from projection.eval.metrics import Identical, Metric, Words, all_metrics, score_step, summarize
from projection.eval.metrics.formats import CorpusArticle, Step
from projection.eval.metrics.text import normalize, tokens

ENTREE = "Les organismes contrôlent la fraude chaque année."
CIBLE = "Les organismes contrôlent la fraude tous les deux ans."
NBSP, NNBSP, RSQUO, NDASH = map(chr, (0x00A0, 0x202F, 0x2019, 0x2013))


def article(numero: str, *lignes: str, supprime: bool = False) -> CorpusArticle:
    return {"numero": numero, "lignes": list(lignes), "supprime": supprime}


def test_normalize():
    raw = f"l{RSQUO}article{NBSP}«{NNBSP}A{NNBSP}»  {NDASH}\n b"
    assert normalize(raw) == 'l\'article " A " - b'
    assert tokens("l'article 2.") == ["l", "'", "article", "2", "."]


def test_words():
    perfect = Words().score(CIBLE, CIBLE)
    assert (perfect["ajoutes"], perfect["retires"], perfect["f1"]) == (0, 0, 1.0)
    # Recopier l'entrée : 2 mots en trop (« chaque année »), 4 manquants (« tous les deux ans »).
    copied = Words().score(ENTREE, CIBLE)
    assert (copied["ajoutes"], copied["retires"]) == (2, 4)
    assert copied["precision"] == 6 / 8 and copied["rappel"] == 6 / 10
    # Deux articles vides (supprimés des deux côtés) : parfait ; un seul vide : nul.
    assert Words().score("", "")["f1"] == 1.0 and Words().score("", CIBLE)["f1"] == 0.0


def test_missing_ne():
    """Un seul mot oublié inverse le sens : les mots le voient à peine, « identiques » le voit."""
    prediction, cible = "Le décret fixe pas les modalités.", "Le décret ne fixe pas les modalités."
    assert Words().score(prediction, cible)["retires"] == 1
    assert Identical().score(prediction, cible) == {"identique": 0.0}


STEP: Step = {
    "id": "DL1:commission",
    "entree": {
        "ref": "B1",
        "articles": [
            article("PREMIER", ENTREE),
            article("2", "Inchangé."),
            article("3", "Supprimé ensuite."),
        ],
    },
    "sortie": {
        "ref": "BTC1",
        "articles": [
            article("PREMIER", CIBLE),
            article("2", "Inchangé."),
            article("3", supprime=True),
            article("3 BIS", "Nouveau."),
        ],
    },
}


def test_default_metrics():
    assert [m.name for m in all_metrics()] == ["identiques", "presence", "mots"]


def test_identity_prediction():
    """Recopier l'entrée : parfait sur les articles inchangés, raté sur ceux que la cible change."""
    rows = score_step(STEP, STEP["entree"]["articles"])
    assert [(r.numero, r.modifie) for r in rows] == [
        ("PREMIER", True),
        ("2", False),
        ("3", True),
        ("3 BIS", True),
    ]
    summary = summarize(rows)
    assert summary["inchanges"].articles == 1
    assert summary["inchanges"].scores["identiques"]["identique"]["moyenne"] == 1.0
    assert summary["modifies"].scores["identiques"]["identique"]["moyenne"] == 0.0
    # L'article 3 est gardé alors que la cible le supprime, le 3 BIS n'est pas créé.
    assert summary["modifies"].scores["presence"]["presence"]["moyenne"] == 1 / 3


def test_perfect_prediction():
    scores = summarize(score_step(STEP, STEP["sortie"]["articles"]))["tous"].scores
    assert scores["identiques"]["identique"]["moyenne"] == 1.0
    assert scores["presence"]["presence"]["moyenne"] == 1.0
    assert scores["mots"]["f1"]["moyenne"] == 1.0


class SameLength(Metric):
    name = "longueur"

    def score(self, prediction: str, cible: str) -> dict[str, float]:
        return {"meme_longueur": float(len(prediction) == len(cible))}


def test_custom_metric():
    """Une métrique = une sous-classe de Metric ; hors du paquet, elle n'est pas par défaut."""
    summary = summarize(score_step(STEP, STEP["sortie"]["articles"], [SameLength()]))
    expected = {"longueur": {"meme_longueur": {"moyenne": 1.0, "mediane": 1.0}}}
    assert summary["tous"].scores == expected
    assert "longueur" not in [m.name for m in all_metrics()]
