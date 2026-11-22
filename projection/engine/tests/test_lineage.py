"""Historique entre étapes : d'où vient un mot, d'amendement en texte."""

from engine import usecases
from engine.domain.documents import Amendment, Article, Text
from engine.domain.tree import Origin
from engine.usecases.lineage import link

LINES = (
    "I. – Le fait de vendre ce produit est puni d'une amende de 4 000 euros.",
    "II. – Le présent article entre en vigueur le 1er janvier 2027. Il s'applique aux contrats.",
)
DEPOSITED = Text("T0", (Article("3", LINES),))
CE5 = Amendment(
    "CE5",
    "ART. 3",
    "<p>À l'alinéa 1, substituer au mot :</p><p>« 4 000 »</p><p>le mot :</p><p>« 10 000 ».</p>",
    id="CE5",
)


def commission():
    """La consolidation de la commission : le texte projeté, avec l'origine de chaque mot."""
    return usecases.consolidate(DEPOSITED, [CE5]).version


def word_id(version, text, nth=1, article="3", paragraph=0):
    words = [w for w in version.find(article).paragraphs[paragraph].words if w.text == text]
    return words[nth - 1].id


def test_a_word_written_by_an_amendment_keeps_its_trail_in_the_next_stage():
    official = Text("T1", (Article("3", tuple(p.text for p in commission().find("3").paragraphs)),))
    next_stage = link(commission(), official)
    word = next_stage.word(word_id(next_stage, "10"))
    assert word.trail == (Origin("T0", "CE5"), Origin("T1"))
    assert word.id.startswith("T1/")


def test_a_word_of_the_deposited_text_is_traced_through_every_text():
    official = Text("T1", (Article("3", commission().find("3").lines),))
    next_stage = link(commission(), official)
    assert next_stage.word(word_id(next_stage, "vendre")).trail == (Origin("T0"), Origin("T1"))


def test_an_official_retouch_is_born_in_the_next_text():
    lines = commission().find("3").lines
    retouched = (lines[0].replace("amende", "sanction pécuniaire"), lines[1])
    next_stage = link(commission(), Text("T1", (Article("3", retouched),)))
    retouch = next_stage.word(word_id(next_stage, "pécuniaire"))
    assert retouch.trail == (Origin("T1"),)
    assert next_stage.word(word_id(next_stage, "euros")).trail[0] == Origin("T0")
    assert next_stage.word(word_id(next_stage, "euros")).origin.approximate is True


def test_an_identical_paragraph_is_linked_for_sure():
    lines = commission().find("3").lines
    next_stage = link(
        commission(), Text("T1", (Article("3", (lines[0], "Autre alinéa nouveau.")),))
    )
    assert next_stage.word(word_id(next_stage, "euros")).origin.approximate is False
    assert next_stage.word(word_id(next_stage, "nouveau", paragraph=1)).trail == (Origin("T1"),)


def test_a_repeated_passage_is_never_guessed():
    previous = Text("T0", (Article("3", ("de la présente loi et de la présente loi",)),))
    next_stage = link(
        usecases.consolidate(previous, []).version,
        Text("T1", (Article("3", ("de la présente loi",)),)),
    )
    assert all(w.trail == (Origin("T1"),) for w in next_stage.find("3").paragraphs[0].words)


def test_an_article_absent_from_the_previous_stage_is_born_in_the_next_one():
    next_stage = link(commission(), Text("T1", (Article("4", ("Un article nouveau.",)),)))
    assert all(w.trail == (Origin("T1"),) for w in next_stage.find("4").paragraphs[0].words)


def test_inserted_paragraph_does_not_shift_the_alignment_of_the_others():
    lines = commission().find("3").lines
    next_stage = link(commission(), Text("T1", (Article("3", ("Nouveau.", *lines)),)))
    assert next_stage.word(word_id(next_stage, "euros", paragraph=1)).trail[0] == Origin("T0")
    assert next_stage.word(word_id(next_stage, "Nouveau")).trail == (Origin("T1"),)


def test_two_unrelated_paragraphs_at_the_same_position_do_not_swap_their_trail():
    previous = Text("T0", (Article("3", ("Le chat dort dans la cuisine.",)),))
    version = usecases.consolidate(previous, []).version
    next_stage = link(version, Text("T1", (Article("3", ("Un chien court dans la rue.",)),)))
    assert all(w.trail == (Origin("T1"),) for w in next_stage.find("3").paragraphs[0].words)


def test_a_repeated_identical_paragraph_is_linked_but_not_for_sure():
    previous = Text("T0", (Article("3", ("(Supprimé)", "Texte.", "(Supprimé)")),))
    next_stage = link(
        usecases.consolidate(previous, []).version,
        Text("T1", (Article("3", ("(Supprimé)", "Texte.")),)),
    )
    assert next_stage.find("3").paragraphs[0].words[1].origin.approximate is True
    assert next_stage.find("3").paragraphs[1].words[0].origin.approximate is False


def test_an_article_number_present_twice_is_never_linked():
    previous = Text("T0", (Article("3", ("Un alinéa de texte.",)),))
    twice = Text("T1", (Article("3", ("Un alinéa de texte.",)), Article("3", ("Autre.",))))
    version = link(usecases.consolidate(previous, []).version, twice)
    assert all(
        w.trail == (Origin("T1"),) for a in version.articles for p in a.paragraphs for w in p.words
    )
