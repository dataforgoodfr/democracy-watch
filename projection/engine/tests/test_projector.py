"""Tests d'intégration de `project` : analyse, application et trace, sur de faux objets."""

import pytest

from engine import usecases
from engine.domain.documents import Amendment, Article, Text
from engine.domain.refusal import Reason
from engine.domain.status import Status
from engine.reading import GRAMMAR_VERSION

LINES = (
    "Le premier alinéa du texte.",
    "Le deuxième alinéa précise les conditions, sauf exception.",
    "Le troisième alinéa est supprimé plus tard.",
)


def article(number="3", lines=LINES, **flags):
    return Article(number, lines, **flags)


def amendment(*paragraphs, article_vise="ART. 3"):
    dispositif = "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
    return Amendment("CE1", article_vise, dispositif)


def project(articles, amendment):
    return usecases.project(Text("T", tuple(articles)), amendment)


def project_lines(*paragraphs, lines=LINES):
    projection = project([article(lines=lines)], amendment(*paragraphs))
    assert projection.applied, projection.detail
    assert projection.result is not None
    return projection.result.lines


def refusal(*paragraphs, articles=None, **kwargs):
    projection = project(articles or [article()], amendment(*paragraphs, **kwargs))
    assert not projection.applied and projection.result is None
    return projection


@pytest.mark.parametrize(
    ("paragraphs", "expected"),
    [
        pytest.param(
            ("À l’alinéa 2, substituer au mot :", "« deuxième »", "le mot :", "« second »."),
            {1: "Le second alinéa précise les conditions, sauf exception."},
            id="substitute",
        ),
        pytest.param(  # recollement
            ("À l’alinéa 2, supprimer les mots :", "« , sauf exception »."),
            {1: "Le deuxième alinéa précise les conditions."},
            id="delete_mots",
        ),
        pytest.param(
            ("À l’alinéa 1, après le mot :", "« premier »,", "insérer les mots :", "« et seul »."),
            {0: "Le premier et seul alinéa du texte."},
            id="insert_mots",
        ),
        pytest.param(
            ("À la fin de l’alinéa 1, insérer les mots :", "« , dans l’ordre »."),
            {0: "Le premier alinéa du texte, dans l'ordre."},
            id="insert_bord_fin",
        ),
        pytest.param(
            ("Au début de l’alinéa 1, insérer les mots :", "« Désormais, »."),
            {0: "Désormais, Le premier alinéa du texte."},
            id="insert_bord_debut",
        ),
        pytest.param(
            ("Compléter l’alinéa 3 par les mots :", "« et ajouté »."),
            {2: "Le troisième alinéa est supprimé plus tard et ajouté."},
            id="complete",
        ),
        pytest.param(
            ("Rédiger ainsi l’alinéa 2 :", "« Nouveau texte. »"),
            {1: "Nouveau texte."},
            id="rewrite",
        ),
        pytest.param(
            (
                "À l’alinéa 2, après le mot :",
                "« conditions »,",
                "rédiger ainsi la fin de l’alinéa :",
                "« et les délais. »",
            ),
            {1: "Le deuxième alinéa précise les conditions et les délais."},
            id="rewrite_fin",
        ),
        pytest.param(
            ("À l’alinéa 2, après le mot :", "« conditions »,", "supprimer la fin de l’alinéa."),
            {1: "Le deuxième alinéa précise les conditions"},
            id="delete_fin",
        ),
    ],
)
def test_single_instruction_text_operations(paragraphs, expected):
    result = project_lines(*paragraphs)
    assert result == tuple(expected.get(i, line) for i, line in enumerate(LINES))


def test_delete_alinea_and_article():
    assert project_lines("Supprimer l’alinéa 3.") == LINES[:2]
    projection = project([article()], amendment("Supprimer cet article."))
    assert projection.result is not None
    assert (projection.result.lines, projection.result.deleted) == ((), True)


@pytest.mark.parametrize(
    ("paragraphs", "expected"),
    [
        pytest.param(  # b_insert_node
            ("Après l’alinéa 1, insérer les deux alinéas suivants :", "« A.", "« B. »"),
            (LINES[0], "A.", "B.", LINES[1], LINES[2]),
            id="insert_after",
        ),
        pytest.param(  # b_insert_node avant
            ("Avant l’alinéa 2, insérer l’alinéa suivant :", "« Avant. »"),
            (LINES[0], "Avant.", LINES[1], LINES[2]),
            id="insert_before",
        ),
        pytest.param(  # b_complete
            ("Compléter cet article par un alinéa ainsi rédigé :", "« Fin. »"),
            (*LINES, "Fin."),
            id="complete_article",
        ),
        pytest.param(  # b_insert_debut
            ("Au début de cet article, insérer l’alinéa suivant :", "« Début. »"),
            ("Début.", *LINES),
            id="insert_debut",
        ),
        pytest.param(  # b_rewrite_compte
            ("Substituer aux alinéas 2 et 3 les deux alinéas suivants :", "« X.", "« Y. »"),
            (LINES[0], "X.", "Y."),
            id="rewrite_range",
        ),
        pytest.param(  # b_rewrite sur l'article entier
            ("Rédiger ainsi cet article :", "« Un.", "« Deux.", "« Trois. »"),
            ("Un.", "Deux.", "Trois."),
            id="rewrite_article",
        ),
    ],
)
def test_block_operations(paragraphs, expected):
    assert project_lines(*paragraphs) == expected


def test_multi_instruction_applies_on_original_positions():
    result = project_lines(
        "I. – À l’alinéa 1, supprimer les mots : « du texte ».",
        "II. – Après l’alinéa 1, insérer l’alinéa suivant :",
        "« Inséré. »",
        "III. – À l’alinéa 3, supprimer les mots : « plus tard ».",
    )
    assert result == (
        "Le premier alinéa.",
        "Inséré.",
        LINES[1],
        "Le troisième alinéa est supprimé.",
    )


def test_trace_records_before_after_and_grammar_version():
    projection = project(
        [article()], amendment("À l’alinéa 2, supprimer les mots : « , sauf exception ».")
    )
    (instruction,) = projection.instructions
    assert instruction.operation is not None and instruction.reason is None
    assert (instruction.before, instruction.after) == (
        (LINES[1],),
        ("Le deuxième alinéa précise les conditions.",),
    )
    assert (projection.amendment, projection.article) == ("CE1", "3")
    assert projection.grammar_version == GRAMMAR_VERSION


def test_all_or_nothing_keeps_the_trace_of_every_instruction():
    projection = refusal(
        "I. – À l’alinéa 1, supprimer les mots : « du texte ».",
        "II. – À l’alinéa 3, supprimer les mots : « absent ».",
    )
    assert projection.reason is Reason.QUOTE_MISSING and "absent" in projection.detail
    assert (projection.amendment, projection.article) == ("CE1", "3")
    first, second = projection.instructions
    assert first.reason is None and first.after == ("Le premier alinéa.",)
    assert second.reason is Reason.QUOTE_MISSING


def test_overlapping_instructions_are_both_in_conflict():
    projection = refusal(
        "I. – À l’alinéa 2, supprimer les mots : « , sauf exception ».",
        "II. – À l’alinéa 2, supprimer les mots : « sauf ».",
    )
    assert projection.reason is Reason.CONFLICT
    assert [i.reason for i in projection.instructions] == [Reason.CONFLICT, Reason.CONFLICT]


def test_disjoint_words_of_the_same_alinea_are_composed():
    lines = project_lines(
        "I. – À l’alinéa 2, supprimer les mots : « , sauf exception ».",
        "II. – À l’alinéa 2, substituer au mot : « précise », le mot : « fixe ».",
    )
    assert lines[1] == "Le deuxième alinéa fixe les conditions."


def test_touching_words_of_the_same_alinea_conflict():
    """Deux modifications contiguës : les espaces à leur jonction dépendent des deux."""
    projection = refusal(
        "I. – À l’alinéa 2, supprimer les mots : « précise ».",
        "II. – À l’alinéa 2, supprimer les mots : « les ».",
    )
    assert projection.reason is Reason.CONFLICT


def test_deleting_the_article_conflicts_with_any_other_instruction():
    projection = refusal(
        "I. – Supprimer cet article.",
        "II. – Au début de cet article, insérer l’alinéa suivant :",
        "« Début. »",
    )
    assert projection.reason is Reason.CONFLICT


@pytest.mark.parametrize(
    ("paragraphs", "reason"),
    [
        (("Cet article est contraire à la Constitution.",), Reason.OUT_OF_SCOPE),
        (("À l’alinéa 9, supprimer les mots : « a ».",), Reason.TARGET_NOT_FOUND),
        (("À l’alinéa 1, supprimer les mots : « absent ».",), Reason.QUOTE_MISSING),
        (("À l’alinéa 2, supprimer les mots : « alinéa » ; « le ».",), Reason.OUT_OF_SCOPE),
        (("Supprimer l’article 4.",), Reason.UNRESOLVED_ARTICLE),  # autre article
        (("Après l’article 3, insérer l’alinéa suivant :", "« X. »"), Reason.OUT_OF_SCOPE),
        (("À la même phrase, supprimer les mots : « a ».",), Reason.OUT_OF_SCOPE),
        (("À l’alinéa 1, après le mot : « alinéa », insérer :",), Reason.OUT_OF_SCOPE),
        (
            ("Après l’alinéa 1, insérer les trois alinéas suivants :", "« A. »", "« B. »"),
            Reason.INCONSISTENT_BLOCK,
        ),
    ],
)
def test_refusals_carry_their_reason(paragraphs, reason):
    assert refusal(*paragraphs).reason is reason


def test_anchor_must_be_unique_in_the_alinea():
    lines = ("Le chat voit le chat.",)
    projection = project(
        [article(lines=lines)], amendment("À l’alinéa 1, supprimer les mots : « chat ».")
    )
    assert projection.reason is Reason.QUOTE_MULTIPLE
    ordinal = amendment("À l’alinéa 1, supprimer la seconde occurrence du mot : « chat ».")
    result = project([article(lines=lines)], ordinal).result
    assert result is not None and result.lines == ("Le chat voit le.",)


@pytest.mark.parametrize(
    ("label", "reason"),
    [
        (None, Reason.UNRESOLVED_ARTICLE),
        ("", Reason.UNRESOLVED_ARTICLE),
        ("APRÈS ART. 3", Reason.OUT_OF_SCOPE),
        ("AVANT ART. 3", Reason.OUT_OF_SCOPE),
        ("TITRE", Reason.OUT_OF_SCOPE),
        ("ART. 3 À 5", Reason.UNRESOLVED_ARTICLE),
        ("ART. 3 ET 4", Reason.UNRESOLVED_ARTICLE),
    ],
)
def test_article_label_refusals(label, reason):
    projection = project([article()], amendment("Supprimer cet article.", article_vise=label))
    assert (projection.reason, projection.article) == (reason, None)
    assert projection.instructions == ()


@pytest.mark.parametrize(
    "articles",
    [
        pytest.param([article("4")], id="absent"),
        pytest.param([article(), article()], id="doublon"),
        pytest.param([article(lines=(), unchanged=True)], id="inchange"),
        pytest.param([article(from_range=True)], id="plage"),
    ],
)
def test_article_must_be_found_once_with_its_own_text(articles):
    projection = project(articles, amendment("Supprimer l’alinéa 1."))
    assert projection.reason is Reason.UNRESOLVED_ARTICLE


def test_both_sides_are_normalized_before_comparison():
    lines = ("Le mot : l’exemple‑type.",)
    result = project_lines("À l’alinéa 1, supprimer les mots : « l’exemple‑type ».", lines=lines)
    assert result == ("Le mot :.",)


def test_projection_is_pure():
    articles, current = [article()], amendment("Supprimer l’alinéa 3.")
    assert project(articles, current) == project(articles, current)


def test_first_refused_instruction_gives_the_projection_reason():
    projection = refusal(
        "I. – À l’alinéa 1, supprimer les mots : « absent ».",
        "II. – À l’alinéa 9, supprimer les mots : « a ».",
    )
    assert projection.reason is Reason.QUOTE_MISSING
    assert [i.reason for i in projection.instructions] == [
        Reason.QUOTE_MISSING,
        Reason.TARGET_NOT_FOUND,
    ]


@pytest.mark.parametrize(
    ("paragraphs", "reason"),
    [
        pytest.param(  # marqueurs hors suite
            ("I. – Supprimer l’alinéa 1.", "III. – Supprimer l’alinéa 2."),
            Reason.AMBIGUOUS,
            id="markers_out_of_sequence",
        ),
        pytest.param(  # deux cibles contradictoires dans une instruction
            ("À l’alinéa 2, supprimer l’alinéa 3.",), Reason.AMBIGUOUS, id="two_targets"
        ),
        pytest.param(  # alinéa cité vide
            ("Après l’alinéa 1, insérer l’alinéa suivant :", "« »"),
            Reason.INCONSISTENT_BLOCK,
            id="empty_block",
        ),
        pytest.param(  # alinéa sans « ouvrant
            ("Après l’alinéa 1, insérer les deux alinéas suivants :", "« A.", "B. »"),
            Reason.INCONSISTENT_BLOCK,
            id="block_without_opening_quote",
        ),
        pytest.param(  # « les alinéas suivants » seulement dans la dernière instruction
            (
                "I. – Compléter cet article par les alinéas suivants :",
                "« A. »",
                "II. – Supprimer l’alinéa 1.",
            ),
            Reason.INCONSISTENT_BLOCK,
            id="alineas_sans_nombre_not_last",
        ),
        pytest.param(  # une citation ne s'étend pas sur plusieurs alinéas
            ("Rédiger ainsi l’alinéa 1 :", "« a", "b »."), Reason.INCONSISTENT_BLOCK, id="multiline"
        ),
        pytest.param(  # « Rétablir » ne remplace pas un alinéa existant
            ("Rétablir l’alinéa 2 dans la rédaction suivante :", "« Rétabli. »"),
            Reason.OUT_OF_SCOPE,
            id="restore",
        ),
        pytest.param(  # le préfixe « à la fin » ne s'applique pas à une suppression de mots
            ("À la fin de l’alinéa 1, supprimer le mot : « Le ».",),
            Reason.OUT_OF_SCOPE,
            id="edge_prefix_on_delete",
        ),
    ],
)
def test_more_refusals(paragraphs, reason):
    assert refusal(*paragraphs).reason is reason


def test_html_outside_paragraphs_is_refused_not_dropped():
    current = Amendment("CE1", "ART. 3", "Texte libre<p>Supprimer l’alinéa 1.</p>")
    projection = project([article()], current)
    assert projection.reason is Reason.OUT_OF_SCOPE and projection.article == "3"


def test_adjacent_insertions_at_the_same_point_conflict():
    projection = refusal(
        "I. – Après l’alinéa 1, insérer l’alinéa suivant :",
        "« A. »",
        "II. – Avant l’alinéa 2, insérer l’alinéa suivant :",
        "« B. »",
    )
    assert [i.reason for i in projection.instructions] == [Reason.CONFLICT, Reason.CONFLICT]


def test_deleting_an_alinea_is_disjoint_from_editing_another():
    result = project_lines(
        "I. – Supprimer l’alinéa 1.",
        "II. – À l’alinéa 3, supprimer les mots : « plus tard ».",
    )
    assert result == (LINES[1], "Le troisième alinéa est supprimé.")


@pytest.mark.parametrize("label", ["ART. 3", "ART. 3 "])
def test_citing_the_article_being_amended_is_allowed(label):
    projection = project([article()], amendment("Supprimer l’article 3.", article_vise=label))
    assert projection.result is not None and projection.result.deleted


@pytest.mark.parametrize("number", ["30", "3 BIS"])
def test_article_number_must_match_exactly(number):
    projection = project([article(number)], amendment("Supprimer l’alinéa 1."))
    assert projection.reason is Reason.UNRESOLVED_ARTICLE


def test_anchor_search_is_case_sensitive():
    lines = ("Le Chat et le chat.",)
    assert project_lines("À l’alinéa 1, supprimer le mot : « chat ».", lines=lines) == (
        "Le Chat et le.",
    )
    projection = project(
        [article(lines=("Le Chat.",))], amendment("À l’alinéa 1, supprimer le mot : « chat ».")
    )
    assert projection.reason is Reason.QUOTE_MISSING


def test_input_article_is_not_mutated():
    base = article()
    project([base], amendment("Supprimer l’alinéa 3."))
    assert base.lines == LINES


@pytest.mark.parametrize(
    "border",
    [
        ("Compléter cet article par l’alinéa suivant :", "« Ajout. »"),
        ("Au début de cet article, insérer l’alinéa suivant :", "« Ajout. »"),
        ("Après l’alinéa 3, insérer l’alinéa suivant :", "« Ajout. »"),
    ],
)
@pytest.mark.parametrize(
    "replacing",
    [
        ("Rédiger ainsi cet article :", "« Nouveau texte. »"),
        ("Supprimer cet article.",),
    ],
)
def test_border_insertion_conflicts_with_article_replacement(border, replacing):
    projection = refusal("I. – " + replacing[0], *replacing[1:], "II. – " + border[0], *border[1:])
    assert projection.reason is Reason.CONFLICT
    assert [i.reason for i in projection.instructions] == [Reason.CONFLICT, Reason.CONFLICT]


@pytest.mark.parametrize(
    ("paragraphs", "lines"),
    [
        (("Supprimer l’alinéa 1.",), ("Seul alinéa.",)),
        (("Supprimer les alinéas 1 à 3.",), LINES),
    ],
)
def test_deleting_every_alinea_is_refused_instead_of_an_empty_result(paragraphs, lines):
    projection = refusal(*paragraphs, articles=[article(lines=lines)])
    assert projection.reason is Reason.OUT_OF_SCOPE
    assert projection.detail == "tous les alinéas supprimés : supprimer l'article"


def test_instructions_that_together_delete_every_alinea_are_refused():
    projection = refusal(
        "I. – Supprimer l’alinéa 1.",
        "II. – Supprimer l’alinéa 2.",
        articles=[article(lines=LINES[:2])],
    )
    assert projection.reason is Reason.OUT_OF_SCOPE
    assert [i.reason for i in projection.instructions] == [Reason.OUT_OF_SCOPE] * 2


def test_applied_amendment_has_status_applied():
    projection = project(
        [article()],
        amendment("À l’alinéa 2, substituer au mot :", "« deuxième »", "le mot :", "« second »."),
    )
    assert projection.status is Status.APPLIED


def test_ambiguous_amendment_has_status_ambiguous():
    projection = refusal("I. – Supprimer l’alinéa 1.", "III. – Supprimer l’alinéa 2.")
    assert projection.status is Status.AMBIGUOUS
