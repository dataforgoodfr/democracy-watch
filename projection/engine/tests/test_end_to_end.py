"""Bout en bout : charges utiles Tricoteuses synthétiques → adaptateur → moteur → texte résultant.

Sans réseau : on utilise les fonctions pures de l'adaptateur sur des payloads écrits à la main.
"""

import pytest
from datasources import tricoteuses

from engine.adapters import tricoteuses as adapter
from engine.domain.refusal import Reason
from engine.usecases import project

DOCUMENT = {
    "uid": "PIONTEST",
    "titrePrincipal": "Proposition de loi de test",
    "subdivisions": [
        {"type": "Article", "hash": "h1", "titre": "Article 1er", "sequence": 1},
        {"type": "Article", "hash": "h2", "titre": "Article 2 (nouveau)", "sequence": 2},
        {"type": "Article", "hash": "h3", "titre": "Articles 3 à 4", "sequence": 3},
        {"type": "Article", "hash": "h5", "titre": "Article 5", "sequence": 4},
    ],
    "alineas": [
        {"articleRefHash": "h1", "numero": 1, "texte": "L’État publie un rapport annuel."},
        {"articleRefHash": "h2", "numero": 0, "texte": "(Non modifié)"},
        {"articleRefHash": "h2", "numero": 1, "texte": "Le premier alinéa fixe la durée."},
        {"articleRefHash": "h2", "numero": 2, "texte": "Le second alinéa fixe le taux de 5 %."},
        {"articleRefHash": "h3", "numero": 1, "texte": "Texte partagé."},
        {"articleRefHash": "h5", "numero": 0, "texte": "(Conforme)"},
    ],
}
TEXT = adapter.text_from(DOCUMENT["uid"], tricoteuses.articles_from_document(DOCUMENT))


def amendement(dispositif, article_vise, **extra):
    return adapter.amendment_from(
        tricoteuses.amendement_from(
            {
                "uid": "AM1",
                "numeroLong": "CE1",
                "documentRefUid": "PIONTEST",
                "divisionArticleDesignationCourte": article_vise,
                "alineaDesignation": "Alinéa 99",  # indice trompeur : le dispositif prime
                "dispositifHtml": dispositif,
                "sortAmendement": "Adopté",
                **extra,
            }
        )
    )


def test_substitution_on_html_with_entities_and_typographic_spaces():
    dispositif = (
        "<p>À l&#8217;alinéa&nbsp;1, substituer au mot&nbsp;:</p>"
        "<p>&laquo;&nbsp;annuel&nbsp;&raquo;</p>"
        "<p>le mot&nbsp;:</p><p>&laquo;&nbsp;semestriel&nbsp;&raquo;.</p>"
    )
    projection = project(TEXT, amendement(dispositif, "ART. PREMIER"))
    assert projection.result is not None
    assert projection.result.number == "PREMIER"
    assert projection.result.lines == ("L'État publie un rapport semestriel.",)


def test_alinea_numbers_ignore_the_mention_line_of_the_article():
    # « (Non modifié) » n'est pas un alinéa : l'alinéa 2 est bien « Le second alinéa… ».
    dispositif = "<p>Supprimer l&#8217;alinéa 2.</p>"
    projection = project(TEXT, amendement(dispositif, "ART. 2"))
    assert projection.result is not None
    assert projection.result.lines == ("Le premier alinéa fixe la durée.",)


def test_block_insertion_and_trace():
    dispositif = (
        "<p>Après l’alinéa 1, insérer les deux alinéas suivants&nbsp;:</p>"
        "<p>«&nbsp;Un.</p><p>«&nbsp;Deux.&nbsp;»</p>"
    )
    projection = project(TEXT, amendement(dispositif, "ART. 2"))
    assert projection.result is not None
    assert projection.result.lines == (
        "Le premier alinéa fixe la durée.",
        "Un.",
        "Deux.",
        "Le second alinéa fixe le taux de 5 %.",
    )
    (instruction,) = projection.instructions
    assert instruction.before == () and instruction.after == ("Un.", "Deux.")


@pytest.mark.parametrize(
    ("article_vise", "reason"),
    [
        ("ART. 3", Reason.UNRESOLVED_ARTICLE),  # plage « Articles 3 à 4 » : texte partagé
        ("ART. 5", Reason.UNRESOLVED_ARTICLE),  # « (Conforme) » : texte à prendre ailleurs
    ],
)
def test_unresolved_articles_are_refused(article_vise, reason):
    projection = project(TEXT, amendement("<p>Supprimer l’alinéa 1.</p>", article_vise))
    assert (projection.applied, projection.reason) == (False, reason)
