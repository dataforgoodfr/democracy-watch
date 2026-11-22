"""Version, effet et rejeu : un amendement relu contre la version courante, cible lue dans la
version de référence."""

import dataclasses

import pytest

from engine import usecases
from engine.domain.documents import Amendment, Article, Text
from engine.domain.effect import effect_of
from engine.domain.patch import Splice
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, Anaphor, WholeArticle, remap
from engine.domain.tree import article_of
from engine.domain.version import Version
from engine.usecases.draft import draft
from engine.usecases.replay import replay

LINES = (
    "I. – Le fait de vendre ce produit est puni d'une amende de 4 000 euros.",
    "II. – Le présent article entre en vigueur le 1er janvier 2027.",
)
TEXT = Text("T0", (Article("3", LINES),))


def amendment(number, *paragraphs):
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return Amendment(number, "ART. 3", body, id=number)


CE5 = amendment("CE5", "À l'alinéa 1, substituer au mot :", "« 4 000 »", "le mot :", "« 10 000 ».")
CE2 = amendment("CE2", "Avant l'alinéa 1, insérer l'alinéa suivant :", "« Un nouvel alinéa. »")
CE3 = amendment("CE3", "Rédiger ainsi l'alinéa 1 :", "« Alinéa entièrement réécrit. »")
CE4 = amendment("CE4", "À l'alinéa 1, substituer au mot :", "« vendre »", "le mot :", "« céder ».")


def run(*amendments):
    reference = Version.of(TEXT)
    version = reference
    for one in amendments:
        version, _ = replay(version, reference, draft(TEXT, one))
    return reference, version


def test_version_of_text_is_the_reference_and_shares_unchanged_articles():
    reference, version = run(CE5)
    assert version.parent is reference
    assert version.applied == ("CE5",)
    assert reference.applied == ()
    other = Text("T0", (Article("3", LINES), Article("4", ("Autre.",))))
    before = Version.of(other)
    draft_ = draft(other, CE5)
    after, _ = replay(before, before, draft_)
    assert after.find("4") is before.find("4")


def test_replay_matches_project_on_a_fresh_version():
    _, version = run(CE5)
    projected = usecases.project(TEXT, CE5)
    assert projected.result is not None
    assert version.find("3").lines == projected.result.lines


def test_earlier_insertion_does_not_shift_the_target():
    """CE2 est adopté avant : l'alinéa 1 de CE5 reste l'alinéa du texte d'entrée."""
    _, version = run(CE2, CE5)
    lines = version.find("3").lines
    assert lines[1].startswith("I. – Le fait de vendre")
    assert "10 000 euros" in lines[1]
    assert lines[0] == "Un nouvel alinéa."


def test_rewritten_paragraph_makes_the_target_gone():
    reference, version = run(CE3)
    with pytest.raises(Refusal) as error:
        replay(version, reference, draft(TEXT, CE5))
    assert error.value.reason is Reason.TARGET_GONE
    assert version.find("3").lines[0] == "Alinéa entièrement réécrit."


def test_words_removed_earlier_make_the_target_gone():
    reference, version = run(CE5)
    with pytest.raises(Refusal) as error:
        replay(version, reference, draft(TEXT, CE5))
    assert error.value.reason is Reason.TARGET_GONE


def test_a_quote_absent_from_the_input_text_is_refused_before_the_replay():
    absent = amendment(
        "CE9", "À l'alinéa 1, substituer au mot :", "« absent »", "le mot :", "« x »."
    )
    reference = Version.of(TEXT)
    with pytest.raises(Refusal) as error:
        replay(reference, reference, draft(TEXT, absent))
    assert error.value.reason is Reason.QUOTE_MISSING


def test_disjoint_amendments_on_the_same_paragraph_compose_and_keep_their_origin():
    _, version = run(CE4, CE5)
    paragraph = version.find("3").paragraphs[0]
    assert "céder" in paragraph.text and "10 000" in paragraph.text
    origins = {w.text: w.origin.amendment for w in paragraph.words}
    assert origins["céder"] == "CE4" and origins["10"] == "CE5"


def test_refused_draft_leaves_the_version_unchanged():
    reference = Version.of(TEXT)
    unreadable = amendment("CE8", "Faire quelque chose d'incompréhensible.")
    with pytest.raises(Refusal) as error:
        replay(reference, reference, draft(TEXT, unreadable))
    assert error.value.reason is Reason.OUT_OF_SCOPE


def test_effect_lists_written_words_and_read_paragraph():
    tree = article_of("T0", Article("3", LINES))
    start = LINES[0].index("4 000")
    effect = effect_of(tree, (Splice("3", (start, start + 5), "10 000", 0),))
    assert effect.reads == {"T0/3/a1"}
    words = tree.paragraphs[0].words
    thousand = next(k for k, w in enumerate(words) if w.text == "000")
    assert effect.writes == {w.id for w in words[thousand - 2 : thousand + 1]}


def test_rewritten_paragraph_interferes_with_a_word_edit_inside_it():
    tree = article_of("T0", Article("3", LINES))
    start = LINES[0].index("vendre")
    word = effect_of(tree, (Splice("3", (start, start + 6), "céder", 0),))
    rewrite = effect_of(tree, (Splice.on_lines("3", 0, 1, ("Nouveau.",)),))
    other = effect_of(tree, (Splice.on_lines("3", 1, 2, ("Autre.",)),))
    assert word.interferes(rewrite)
    assert not word.interferes(other)


def test_two_word_edits_in_the_same_paragraph_do_not_interfere():
    tree = article_of("T0", Article("3", LINES))
    a, b = LINES[0].index("vendre"), LINES[0].index("produit")
    first = effect_of(tree, (Splice("3", (a, a + 6), "céder", 0),))
    second = effect_of(tree, (Splice("3", (b, b + 7), "bien", 0),))
    assert not first.interferes(second)


def test_insertions_are_symbolic_positions():
    tree = article_of("T0", Article("3", LINES))
    effect = effect_of(
        tree, (Splice.on_lines("3", 1, 1, ("Un.",)), Splice.on_lines("3", 0, 0, ("Zéro.",)))
    )
    assert effect.writes == {"after:T0/3/a1", "start:T0/3"}


def test_consolidation_exposes_the_resulting_version():
    consolidation = usecases.consolidate(TEXT, [CE5])
    assert consolidation.version.applied == ("CE5",)
    assert consolidation.version.find("3").lines == consolidation.articles[0].lines
    assert consolidation.version.text_uid == "T0"


def test_an_insertion_inside_a_word_writes_that_word():
    tree = article_of("T0", Article("3", ("un chat noir",)))
    inside = effect_of(tree, (Splice("3", (5, 5), "u", 0),))
    delete = effect_of(tree, (Splice("3", (3, 7), "", 0),))
    assert "T0/3/a1/m3" in inside.writes
    assert inside.interferes(delete)


def test_remap_reads_negative_and_whole_article_targets_in_the_reference():
    ref = article_of("T0", Article("3", ("a", "b", "c")))
    current = article_of("T0", Article("3", ("a", "b", "c")))
    current = dataclasses.replace(
        current,
        paragraphs=(article_of("X", Article("3", ("z",))).paragraphs[0], *current.paragraphs),
    )
    assert remap(Alineas((-1,)), ref, current) == Alineas((4,))
    assert remap(WholeArticle(), ref, current) == WholeArticle()
    assert remap(Anaphor(), ref, current) == Anaphor()
    gone = dataclasses.replace(current, paragraphs=current.paragraphs[:2])
    with pytest.raises(Refusal) as error:
        remap(Alineas((3,)), ref, gone)
    assert error.value.reason is Reason.TARGET_GONE


def test_two_instructions_on_the_same_words_are_refused_as_a_conflict():
    clash = amendment(
        "CE6",
        "I. – À l'alinéa 1, substituer au mot :",
        "« vendre »",
        "le mot :",
        "« céder ».",
        "II. – À l'alinéa 1, substituer au mot :",
        "« vendre »",
        "le mot :",
        "« donner ».",
    )
    reference = Version.of(TEXT)
    with pytest.raises(Refusal) as error:
        replay(reference, reference, draft(TEXT, clash))
    assert error.value.reason is Reason.CONFLICT


def test_emptying_the_article_without_deleting_it_is_refused():
    emptied = amendment("CE7", "Supprimer les alinéas 1 et 2.")
    reference = Version.of(TEXT)
    with pytest.raises(Refusal) as error:
        replay(reference, reference, draft(TEXT, emptied))
    assert error.value.reason is Reason.OUT_OF_SCOPE


def test_deleting_the_article_leaves_a_version_without_paragraphs():
    reference = Version.of(TEXT)
    deleted, _ = replay(
        reference, reference, draft(TEXT, amendment("CE1", "Supprimer cet article."))
    )
    assert deleted.find("3").paragraphs == ()


THREE = Text("T0", (Article("3", ("Un.", "Deux.", "Trois.", "Quatre.")),))


def run_three(*amendments):
    reference = Version.of(THREE)
    version = reference
    for one in amendments:
        version, _ = replay(version, reference, draft(THREE, one))
    return version.find("3").lines


def test_insertion_after_a_deleted_alinea_lands_where_it_was():
    delete = amendment("D", "Supprimer l'alinéa 2.")
    insert = amendment("I", "Après l'alinéa 2, insérer l'alinéa suivant :", "« Neuf. »")
    assert run_three(delete, insert) == ("Un.", "Neuf.", "Trois.", "Quatre.")


def test_insertion_after_a_rewritten_alinea_lands_after_the_replacement():
    rewrite = amendment("R", "Rédiger ainsi l'alinéa 2 :", "« Nouveau. »")
    insert = amendment("I", "Après l'alinéa 2, insérer l'alinéa suivant :", "« Neuf. »")
    assert run_three(rewrite, insert) == ("Un.", "Nouveau.", "Neuf.", "Trois.", "Quatre.")


def test_insertion_before_a_deleted_alinea_lands_after_the_previous_one():
    delete = amendment("D", "Supprimer l'alinéa 2.")
    insert = amendment("I", "Avant l'alinéa 2, insérer l'alinéa suivant :", "« Neuf. »")
    assert run_three(delete, insert) == ("Un.", "Neuf.", "Trois.", "Quatre.")


def test_insertion_after_the_last_alinea_deleted_goes_to_the_end():
    delete = amendment("D", "Supprimer l'alinéa 4.")
    insert = amendment("I", "Après l'alinéa 4, insérer l'alinéa suivant :", "« Neuf. »")
    assert run_three(delete, insert) == ("Un.", "Deux.", "Trois.", "Neuf.")


def test_insertion_before_the_first_alinea_deleted_goes_to_the_start():
    delete = amendment("D", "Supprimer l'alinéa 1.")
    insert = amendment("I", "Avant l'alinéa 1, insérer l'alinéa suivant :", "« Neuf. »")
    assert run_three(delete, insert) == ("Neuf.", "Deux.", "Trois.", "Quatre.")


def test_word_edit_in_a_deleted_alinea_is_still_gone():
    delete = amendment("D", "Supprimer l'alinéa 2.")
    edit = amendment("E", "À l'alinéa 2, substituer au mot :", "« Deux »", "le mot :", "« Dix ».")
    with pytest.raises(Refusal) as error:
        run_three(delete, edit)
    assert error.value.reason is Reason.TARGET_GONE
