"""Tests de `consolidate` sur de faux objets, puis bout en bout Tricoteuses."""

import dataclasses

import pytest
from datasources import tricoteuses

from engine import usecases
from engine.adapters import tricoteuses as adapter
from engine.domain.documents import Amendment, Article, Text
from engine.domain.refusal import Reason

LINES = (
    "Le premier alinéa du texte.",
    "Le deuxième alinéa précise les conditions.",
    "Le troisième alinéa est supprimé plus tard.",
)


def article(number="3", lines=LINES, **flags):
    return Article(number, lines, **flags)


def project(articles, amendment):
    return usecases.project(Text("T", tuple(articles)), amendment)


def consolidate(articles, amendments):
    return usecases.consolidate(Text("T", tuple(articles)), amendments)


def amendment(*paragraphs, numero="CE1", article_vise="ART. 3", uid=None, **extra):
    dispositif = "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
    return Amendment(
        number=numero,
        target_label=article_vise,
        body_html=dispositif,
        id=uid or f"UID-{numero}",
        parent_id=extra.pop("parent_uid", None),
        twin_group=extra.pop("id_identique", None),
    )


FIRST = ("À l’alinéa 1, substituer au mot :", "« premier »", "le mot :", "« seul ».")
SECOND = ("À l’alinéa 2, substituer au mot :", "« deuxième »", "le mot :", "« second ».")
DELETE_FIRST = ("Supprimer l’alinéa 1.",)
INSERT_AFTER_1 = ("Après l’alinéa 1, insérer l’alinéa suivant :", "« Nouveau. »")
INSERT_AFTER_1_BIS = ("Après l’alinéa 1, insérer l’alinéa suivant :", "« Autre. »")
DELETE_ARTICLE = ("Supprimer cet article.",)


def test_distinct_alineas_are_composed():
    result = consolidate(
        [article()], [amendment(*FIRST, numero="CE1"), amendment(*SECOND, numero="CE2")]
    )
    assert [p.applied for p in result.projections] == [True, True]
    (consolidated,) = result.articles
    assert consolidated.lines == (
        "Le seul alinéa du texte.",
        "Le second alinéa précise les conditions.",
        "Le troisième alinéa est supprimé plus tard.",
    )


def test_each_projection_applies_its_amendment_alone():
    amendments = [amendment(*FIRST, numero="CE1"), amendment(*SECOND, numero="CE2")]
    result = consolidate([article()], amendments)
    assert result.projections[0].result is not None
    assert result.projections[0].result.lines[1] == LINES[1]
    assert result.projections[1].result is not None
    assert result.projections[1].result.lines[0] == LINES[0]


def test_same_alinea_conflicts_for_both():
    other = ("À l’alinéa 1, substituer au mot :", "« premier »", "le mot :", "« unique ».")
    result = consolidate([article()], [amendment(*FIRST), amendment(*other, numero="CE2")])
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT]
    assert all(i.reason is Reason.CONFLICT for p in result.projections for i in p.instructions)
    assert result.articles == ()


def test_two_insertions_at_the_same_point_conflict():
    result = consolidate(
        [article()],
        [amendment(*INSERT_AFTER_1), amendment(*INSERT_AFTER_1_BIS, numero="CE2")],
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT]


def test_article_deletion_conflicts_with_another_amendment():
    result = consolidate(
        [article()], [amendment(*DELETE_ARTICLE), amendment(*SECOND, numero="CE2")]
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT]


def test_conflict_spares_unrelated_amendment():
    result = consolidate(
        [article()],
        [
            amendment(*DELETE_FIRST),
            amendment(*FIRST, numero="CE2"),
            amendment(*SECOND, numero="CE3"),
        ],
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT, None]
    assert result.articles == ()


def test_already_refused_amendment_does_not_conflict_with_others():
    # CE1 touche l'alinéa 1 mais sa seconde instruction est refusée : elle ne bloque pas CE2.
    partly_absent = (
        "I. – À l’alinéa 1, substituer au mot : « premier » le mot : « seul ».",
        "II. – À l’alinéa 2, substituer au mot : « absent » le mot : « x ».",
    )
    result = consolidate(
        [article()],
        [amendment(*partly_absent, numero="CE1"), amendment(*DELETE_FIRST, numero="CE2")],
    )
    assert [p.reason for p in result.projections] == [Reason.QUOTE_MISSING, None]


def test_identical_amendments_are_merged():
    result = consolidate(
        [article()],
        [
            amendment(*FIRST, numero="CE1", id_identique="7"),
            amendment(*FIRST, numero="CE2", id_identique="7"),
        ],
    )
    first, second = result.projections
    assert (first.amendment, second.amendment) == ("CE1", "CE2")
    assert first.applied and second.result == first.result
    (consolidated,) = result.articles
    assert consolidated.lines[0] == "Le seul alinéa du texte."


@pytest.mark.parametrize(
    "other",
    [
        pytest.param({"id_identique": "8"}, id="other_id"),
        pytest.param({"id_identique": None}, id="no_id"),
    ],
)
def test_identical_amendments_are_not_merged_without_the_same_id(other):
    result = consolidate(
        [article()],
        [
            amendment(*FIRST, numero="CE1", id_identique="7"),
            amendment(*FIRST, numero="CE2", **{"id_identique": "7"} | other),
        ],
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT]


def test_same_id_but_different_dispositif_is_not_merged():
    result = consolidate(
        [article()],
        [
            amendment(*INSERT_AFTER_1, numero="CE1", id_identique="7"),
            amendment(*INSERT_AFTER_1_BIS, numero="CE2", id_identique="7"),
        ],
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT]


def test_same_id_and_dispositif_on_other_article_is_not_merged():
    result = consolidate(
        [article("3"), article("4")],
        [
            amendment(*FIRST, numero="CE1", id_identique="7", article_vise="ART. 3"),
            amendment(*FIRST, numero="CE2", id_identique="7", article_vise="ART. 4"),
        ],
    )
    assert [p.article for p in result.projections] == ["3", "4"]
    assert [r.number for r in result.articles] == ["3", "4"]


def test_sub_amendment_and_its_parent_are_out_of_scope():
    result = consolidate(
        [article()],
        [
            amendment(*FIRST, numero="CE1", uid="PARENT"),
            amendment(*SECOND, numero="CE2", parent_uid="PARENT"),
            amendment("Supprimer l’alinéa 3.", numero="CE3"),
        ],
    )
    assert [p.reason for p in result.projections] == [
        Reason.OUT_OF_SCOPE,
        Reason.OUT_OF_SCOPE,
        None,
    ]
    assert "sous-amendement" in result.projections[0].detail
    assert "sous-amendement" in result.projections[1].detail
    # Le parent refusé pourrait modifier l'article : pas de texte consolidé.
    assert result.articles == ()


def test_article_is_not_consolidated_if_one_amendment_is_refused():
    absent = ("À l’alinéa 2, substituer au mot :", "« absent »", "le mot :", "« x ».")
    result = consolidate([article()], [amendment(*FIRST), amendment(*absent, numero="CE2")])
    assert [p.reason for p in result.projections] == [None, Reason.QUOTE_MISSING]
    assert result.articles == ()


@pytest.mark.parametrize("article_vise", [None, "ART. 3 À 5", "ART. 3 ET 4"])
def test_amendment_with_unknown_target_blocks_every_article(article_vise):
    result = consolidate(
        [article("3"), article("4")],
        [
            amendment(*FIRST, numero="CE1", article_vise="ART. 3"),
            amendment(*FIRST, numero="CE2", article_vise=article_vise),
        ],
    )
    assert [p.reason for p in result.projections] == [None, Reason.UNRESOLVED_ARTICLE]
    assert result.projections[1].article is None
    assert result.articles == ()


def test_sub_amendment_after_article_is_out_of_scope_without_target():
    result = consolidate(
        [article()],
        [
            amendment(*FIRST, numero="CE1", uid="PARENT"),
            amendment(*FIRST, numero="CE2", parent_uid="PARENT", article_vise="APRÈS ART. 3"),
        ],
    )
    sub = result.projections[1]
    assert (sub.article, sub.reason) == (None, Reason.OUT_OF_SCOPE)


@pytest.mark.parametrize("flags", [{"unchanged": True}, {"from_range": True}])
def test_article_without_known_text_refuses_its_amendment(flags):
    result = consolidate([article(**flags)], [amendment(*FIRST)])
    assert [p.reason for p in result.projections] == [Reason.UNRESOLVED_ARTICLE]
    assert result.articles == ()


def test_conflict_on_one_article_spares_the_other():
    result = consolidate(
        [article("3"), article("4")],
        [
            amendment(*FIRST, numero="CE1", article_vise="ART. 3"),
            amendment(*DELETE_FIRST, numero="CE2", article_vise="ART. 3"),
            amendment(*FIRST, numero="CE3", article_vise="ART. 4"),
        ],
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT, None]
    assert [r.number for r in result.articles] == ["4"]


def test_identical_dispositif_without_id_is_not_merged():
    result = consolidate(
        [article()], [amendment(*FIRST, numero="CE1"), amendment(*FIRST, numero="CE2")]
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT, Reason.CONFLICT]


def test_identical_amendments_conflicting_with_a_third_are_all_in_conflict():
    other = ("À l’alinéa 1, substituer au mot :", "« premier »", "le mot :", "« unique ».")
    result = consolidate(
        [article()],
        [
            amendment(*FIRST, numero="CE1", id_identique="7"),
            amendment(*FIRST, numero="CE2", id_identique="7"),
            amendment(*other, numero="CE3"),
        ],
    )
    assert [p.reason for p in result.projections] == [Reason.CONFLICT] * 3
    assert [p.amendment for p in result.projections] == ["CE1", "CE2", "CE3"]
    assert result.articles == ()


def test_copy_of_a_refused_representative_carries_the_same_refusal():
    absent = ("À l’alinéa 1, substituer au mot :", "« absent »", "le mot :", "« x ».")
    result = consolidate(
        [article()],
        [
            amendment(*absent, numero="CE1", id_identique="7"),
            amendment(*absent, numero="CE2", id_identique="7"),
        ],
    )
    first, copy = result.projections
    assert (copy.amendment, copy.reason) == ("CE2", Reason.QUOTE_MISSING)
    assert copy == dataclasses.replace(first, amendment="CE2")


def test_insertion_after_an_alinea_composes_with_the_replacement_of_the_next_one():
    result = consolidate(
        [article()], [amendment(*INSERT_AFTER_1), amendment(*SECOND, numero="CE2")]
    )
    assert [p.applied for p in result.projections] == [True, True]
    (consolidated,) = result.articles
    assert consolidated.lines == (
        LINES[0],
        "Nouveau.",
        "Le second alinéa précise les conditions.",
        LINES[2],
    )


def test_insertion_after_an_alinea_composes_with_its_replacement():
    after_2 = ("Après l’alinéa 2, insérer l’alinéa suivant :", "« Nouveau. »")
    rewrite_2 = ("Rédiger ainsi l’alinéa 2 :", "« Réécrit. »")
    result = consolidate([article()], [amendment(*after_2), amendment(*rewrite_2, numero="CE2")])
    assert [p.applied for p in result.projections] == [True, True]
    (consolidated,) = result.articles
    assert consolidated.lines == (LINES[0], "Réécrit.", "Nouveau.", LINES[2])


def test_unresolved_article_blocks_only_the_article_it_targets():
    result = consolidate(
        [article("3"), article("4")],
        [
            amendment(*FIRST, numero="CE1", article_vise="ART. 3"),
            amendment(*FIRST, numero="CE2", article_vise="ART. 4"),
            amendment(*FIRST, numero="CE3", article_vise="ART. 9"),
            amendment(*FIRST, numero="CE4", article_vise="APRÈS ART. 3"),
        ],
    )
    assert [p.reason for p in result.projections] == [
        None,
        None,
        Reason.UNRESOLVED_ARTICLE,
        Reason.OUT_OF_SCOPE,
    ]
    assert [r.number for r in result.articles] == ["3", "4"]


def test_articles_follow_the_input_order_and_projections_the_amendment_order():
    result = consolidate(
        [article("4"), article("3")],
        [
            amendment(*FIRST, numero="CE2", article_vise="ART. 3"),
            amendment(*FIRST, numero="CE1", article_vise="ART. 4"),
        ],
    )
    assert [p.amendment for p in result.projections] == ["CE2", "CE1"]
    assert [r.number for r in result.articles] == ["4", "3"]


def test_article_deleted_by_a_lone_amendment():
    result = consolidate([article()], [amendment(*DELETE_ARTICLE)])
    (consolidated,) = result.articles
    assert consolidated.deleted and consolidated.lines == ()


def test_empty_list():
    result = consolidate([article()], [])
    assert result.projections == () and result.articles == ()


def test_single_amendment_matches_project():
    single = amendment(*FIRST)
    result = consolidate([article()], [single])
    assert result.projections == (project([article()], single),)
    assert result.articles == (result.projections[0].result,)


def test_second_stage_uses_the_official_text_not_our_partial_result():
    # la commission est refusée chez nous (citation absente) ; la séance est projetée sur le
    # texte officiel adopté en commission, fourni par l'appelant.
    absent = ("À l’alinéa 1, substituer au mot :", "« absent »", "le mot :", "« x ».")
    commission = consolidate([article()], [amendment(*absent, numero="CE1")])
    assert commission.articles == ()
    official = ("Le premier alinéa adopté en commission.", *LINES[1:])
    validate = ("À l’alinéa 1, substituer au mot :", "« adopté »", "le mot :", "« validé ».")
    seance = consolidate([article(lines=official)], [amendment(*validate, numero="AS1")])
    (consolidated,) = seance.articles
    assert consolidated.lines[0] == "Le premier alinéa validé en commission."


DOCUMENT = {
    "uid": "PIONTEST",
    "subdivisions": [{"type": "Article", "hash": "h1", "titre": "Article 1er", "sequence": 1}],
    "alineas": [
        {"articleRefHash": "h1", "numero": 1, "texte": "Premier alinéa annuel."},
        {"articleRefHash": "h1", "numero": 2, "texte": "Second alinéa fixe."},
    ],
}


def tricoteuses_amendement(uid, numero, dispositif, **extra):
    return adapter.amendment_from(
        tricoteuses.amendement_from(
            {
                "uid": uid,
                "numeroLong": numero,
                "divisionArticleDesignationCourte": "ART. PREMIER",
                "dispositifHtml": dispositif,
                "sortAmendement": "Adopté",
                **extra,
            }
        )
    )


def test_end_to_end_tricoteuses_two_amendments():
    articles = adapter.text_from("PIONTEST", tricoteuses.articles_from_document(DOCUMENT)).articles
    result = consolidate(
        articles,
        [
            tricoteuses_amendement(
                "AM1",
                "CE1",
                "<p>À l&#8217;alinéa&nbsp;1, substituer au mot&nbsp;:</p>"
                "<p>&laquo;&nbsp;annuel&nbsp;&raquo;</p><p>le mot&nbsp;:</p>"
                "<p>&laquo;&nbsp;semestriel&nbsp;&raquo;.</p>",
            ),
            tricoteuses_amendement("AM2", "CE2", "<p>Supprimer l&#8217;alinéa 2.</p>"),
        ],
    )
    assert [p.applied for p in result.projections] == [True, True]
    (consolidated,) = result.articles
    assert (consolidated.number, consolidated.lines) == ("PREMIER", ("Premier alinéa semestriel.",))
