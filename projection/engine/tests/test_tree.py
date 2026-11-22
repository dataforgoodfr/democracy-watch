"""Arbre du texte et identifiants stables."""

import pytest

from engine.domain import identity
from engine.domain.documents import Article
from engine.domain.tree import Origin, Word, article_of, tokenize

LINES = (
    "I. – Le fait de vendre ce produit est puni d'une amende de 4 000 euros.",
    "II. – Le présent article entre en vigueur le 1er janvier 2027. Il s'applique aux contrats.",
)


def test_tokenize_is_lossless():
    for line in (*LINES, "", "  deux  espaces ", "0,5 %", "porte-parole… « oui »"):
        assert "".join(tokenize(line)) == line


def test_tokenize_splits_words_spaces_and_signs():
    assert tokenize("d'une amende.") == ["d", "'", "une", " ", "amende", "."]


def test_identifiers_are_readable():
    assert identity.article_id("T0", "5 BIS") == "T0/5-BIS"
    assert identity.paragraph_id("T0/5-BIS", 3) == "T0/5-BIS/a3"
    assert identity.word_id("T0/5-BIS/a3", 12) == "T0/5-BIS/a3/m12"
    assert identity.written_paragraph_id("CE5", 1) == "CE5/a1"
    assert identity.written_word_id("T0/3/a1", "CE5", 2) == "T0/3/a1/CE5.m2"


def test_article_tree_keeps_text_and_identifies_every_node():
    tree = article_of("T0", Article("3", LINES))
    assert tree.id == "T0/3"
    assert tree.lines == LINES
    assert [p.id for p in tree.paragraphs] == ["T0/3/a1", "T0/3/a2"]
    words = [w for p in tree.paragraphs for w in p.words]
    assert len({w.id for w in words}) == len(words)
    assert words[0] == Word("T0/3/a1/m1", "I", Origin("T0"))
    assert all(w.origin == Origin("T0", None) for w in words)


def test_identifiers_do_not_depend_on_other_paragraphs():
    """Le texte d'un alinéa ne change pas l'identifiant de ses voisins."""
    before = article_of("T0", Article("3", ("a", "b", "c")))
    after = article_of("T0", Article("3", ("a", "autre texte", "c")))
    assert before.paragraphs[2] == after.paragraphs[2]
    assert before.paragraphs[0].id == after.paragraphs[0].id


def test_find_by_identifier_and_missing():
    tree = article_of("T0", Article("3", LINES))
    assert tree.find("T0/3/a2") == 1
    with pytest.raises(ValueError):
        tree.find("T0/3/a9")


def test_trail_runs_from_first_appearance_to_current_origin():
    word = Word("x", "mot", Origin("T1", None), history=(Origin("T0", "CE5"),))
    assert word.trail == (Origin("T0", "CE5"), Origin("T1", None))
    assert Word("y", "mot", Origin("T0")).trail == (Origin("T0"),)
