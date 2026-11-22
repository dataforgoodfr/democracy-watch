"""L'adaptateur Tricoteuses rend des types du moteur et ne reprend que ce que le moteur lit."""

import dataclasses

from datasources import tricoteuses

from engine.adapters import tricoteuses as adapter
from engine.domain.documents import Amendment, Article


def test_text_from_keeps_order_and_flags():
    articles = [
        tricoteuses.Article("PREMIER", ("a", "b")),
        tricoteuses.Article("2", (), inchange=True),
        tricoteuses.Article("3", ("c",), issu_de_plage=True),
    ]
    text = adapter.text_from("PION1", articles)
    assert text.uid == "PION1"
    assert text.articles == (
        Article("PREMIER", ("a", "b")),
        Article("2", (), unchanged=True),
        Article("3", ("c",), from_range=True),
    )


def test_amendment_from_drops_the_alinea_hint():
    amendement = tricoteuses.Amendement(
        uid="AM1",
        numero="CE1",
        texte_ref="PION1",
        article_vise="ART. 2",
        alinea="Alinéa 99",
        dispositif="<p>Supprimer l’alinéa 1.</p>",
        parent_uid="AM0",
        tri_amendement=None,
        date_sort=None,
        id_identique="7",
    )
    amendment = adapter.amendment_from(amendement)
    assert amendment == Amendment(
        number="CE1",
        target_label="ART. 2",
        body_html="<p>Supprimer l’alinéa 1.</p>",
        id="AM1",
        parent_id="AM0",
        twin_group="7",
    )
    assert "alinea" not in {field.name for field in dataclasses.fields(Amendment)}
