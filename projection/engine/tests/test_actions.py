import pytest

from engine.actions import (
    DeleteEnd,
    DeleteNode,
    DeleteWords,
    InsertEdge,
    InsertNode,
    InsertWords,
    Rewrite,
    RewriteEnd,
    Substitute,
)
from engine.domain.documents import Article
from engine.domain.patch import Splice, apply
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, Anaphor, WholeArticle
from engine.domain.writing import Anchor

LINES = ("Un chat.", "Deux chiens.", "Trois oiseaux.")


def plan(operation, lines):
    """Le patch de l'opération contre l'article « 5 » de ces alinéas."""
    return operation.plan(Article("5", lines))


def edit(start, end, new):
    return Splice.on_lines("5", start, end, new)


def article_edit(new):
    return Splice.on_article("5", new)


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        (Substitute(Alineas((2,)), Anchor("chiens"), "loups"), (edit(1, 2, ("Deux loups.",)),)),
        (
            Substitute(Alineas((-1,)), Anchor("Trois"), "Quatre"),
            (edit(2, 3, ("Quatre oiseaux.",)),),
        ),
        # cible multiple : l'ancre est cherchée dans tous les alinéas visés
        (Substitute(Alineas((1, 2)), Anchor("chiens"), "loups"), (edit(1, 2, ("Deux loups.",)),)),
        (Substitute(WholeArticle(), Anchor("oiseaux"), "pies"), (edit(2, 3, ("Trois pies.",)),)),
        (Substitute(Alineas((1,)), Anchor("chat", 1), "rat"), (edit(0, 1, ("Un rat.",)),)),
        (DeleteWords(Alineas((2,)), Anchor("Deux")), (edit(1, 2, ("chiens.",)),)),
        (DeleteWords(Alineas((2,)), Anchor("chiens")), (edit(1, 2, ("Deux.",)),)),
        (DeleteWords(Alineas((1,)), Anchor("Un chat")), (edit(0, 1, (".",)),)),
        (InsertWords(Alineas((1,)), Anchor("Un"), "gros", True), (edit(0, 1, ("Un gros chat.",)),)),
        (
            InsertWords(Alineas((1,)), Anchor("chat"), "gros", False),
            (edit(0, 1, ("Un gros chat.",)),),
        ),
        (
            InsertWords(Alineas((1,)), Anchor("chat"), ", noir", True),
            (edit(0, 1, ("Un chat, noir.",)),),
        ),
        (InsertEdge(Alineas((1,)), "noir", False), (edit(0, 1, ("Un chat noir.",)),)),
        (InsertEdge(Alineas((1,)), "Le", True), (edit(0, 1, ("Le Un chat.",)),)),
        (InsertEdge(Alineas((-1,)), ", noirs", False), (edit(2, 3, ("Trois oiseaux, noirs.",)),)),
        (DeleteNode(Alineas((2,))), (edit(1, 2, ()),)),
        (DeleteNode(Alineas((3, 1))), (edit(0, 1, ()), edit(2, 3, ()))),
        (DeleteNode(WholeArticle()), (article_edit(()),)),
        (DeleteNode(WholeArticle("5")), (article_edit(()),)),
        (Rewrite(Alineas((2,)), ("Neuf.",)), (edit(1, 2, ("Neuf.",)),)),
        (
            Rewrite(Alineas((2, 3)), ("A.", "B.", "C.")),
            (
                edit(
                    1,
                    3,
                    ("A.", "B.", "C."),
                ),
            ),
        ),
        (Rewrite(Alineas((1, 2, 3)), ("Neuf.",)), (edit(0, 3, ("Neuf.",)),)),
        (Rewrite(WholeArticle(), ("A.", "B.")), (article_edit(("A.", "B.")),)),
        (RewriteEnd(Alineas((2,)), Anchor("Deux"), "ou trois"), (edit(1, 2, ("Deux ou trois",)),)),
        (
            RewriteEnd(Alineas((2,)), Anchor("Deux"), ", ou trois."),
            (edit(1, 2, ("Deux, ou trois.",)),),
        ),
        (DeleteEnd(Alineas((2,)), Anchor("Deux")), (edit(1, 2, ("Deux",)),)),
        (DeleteEnd(Alineas((3,)), Anchor("Trois", 1)), (edit(2, 3, ("Trois",)),)),
        (InsertNode(Alineas((2,)), ("Neuf.",), True), (edit(2, 2, ("Neuf.",)),)),
        (InsertNode(Alineas((2,)), ("Neuf.",), False), (edit(1, 1, ("Neuf.",)),)),
        (InsertNode(Alineas((-1,)), ("A.", "B."), True), (edit(3, 3, ("A.", "B.")),)),
        (InsertNode(Alineas((1,)), ("A.",), False), (edit(0, 0, ("A.",)),)),
        (InsertNode(WholeArticle(), ("A.",), True), (edit(3, 3, ("A.",)),)),
        (InsertNode(WholeArticle(), ("A.",), False), (edit(0, 0, ("A.",)),)),
    ],
)
def test_plan(operation, expected):
    assert apply(LINES, plan(operation, LINES)) == apply(LINES, expected)


def test_plan_refuses_emptied_line():
    with pytest.raises(Refusal) as refusal:
        plan(DeleteWords(Alineas((1,)), Anchor("Un chat.")), ("Un chat.",))
    assert refusal.value.reason is Reason.OUT_OF_SCOPE


def test_plan_multiple_target_anchor_in_one_line():
    operation = DeleteWords(Alineas((1, 2)), Anchor("y"))
    assert apply(("a", "b y"), plan(operation, ("a", "b y"))) == ("a", "b")


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        (InsertEdge(WholeArticle(), "noir", False), (edit(0, 1, ("Un chat noir.",)),)),
        (DeleteEnd(Alineas((1,)), Anchor("Un")), (edit(0, 1, ("Un",)),)),
        (RewriteEnd(Alineas((1,)), Anchor("Un"), "chien ;"), (edit(0, 1, ("Un chien ;",)),)),
    ],
)
def test_plan_single_line_article_and_final_punctuation(operation, expected):
    assert apply(("Un chat.",), plan(operation, ("Un chat.",))) == apply(("Un chat.",), expected)


@pytest.mark.parametrize(
    ("operation", "reason"),
    [
        (Substitute(Alineas((4,)), Anchor("chat"), "rat"), Reason.TARGET_NOT_FOUND),
        (DeleteNode(Alineas((0,))), Reason.TARGET_NOT_FOUND),
        (Substitute(WholeArticle("6"), Anchor("chat"), "rat"), Reason.UNRESOLVED_ARTICLE),
        (DeleteNode(WholeArticle("6")), Reason.UNRESOLVED_ARTICLE),
        (Substitute(Anaphor(), Anchor("chat"), "rat"), Reason.OUT_OF_SCOPE),
        (Substitute(Alineas((1,)), Anchor("loup"), "rat"), Reason.QUOTE_MISSING),
        (Substitute(Alineas((2,)), Anchor("Un"), "rat"), Reason.QUOTE_MISSING),
        (DeleteEnd(Alineas((1, 2, 3)), Anchor("Deux", 2)), Reason.QUOTE_MISSING),
        (DeleteWords(WholeArticle(), Anchor("chat", 2)), Reason.QUOTE_MISSING),
        (InsertWords(Alineas((1,)), Anchor("a"), "b", True), Reason.QUOTE_MISSING),
        (DeleteWords(Alineas((1, 2, 3)), Anchor("a")), Reason.QUOTE_MISSING),
        (RewriteEnd(Alineas((1,)), Anchor("loup"), "x"), Reason.QUOTE_MISSING),
        (InsertEdge(Alineas((1, 2)), "x", False), Reason.OUT_OF_SCOPE),
        (InsertEdge(WholeArticle(), "x", False), Reason.OUT_OF_SCOPE),
        (InsertEdge(Alineas((1,)), "noir.", False), Reason.OUT_OF_SCOPE),
        (Rewrite(Alineas((1, 3)), ("x",)), Reason.OUT_OF_SCOPE),
        (InsertNode(Alineas((1, 2)), ("x",), True), Reason.OUT_OF_SCOPE),
        (InsertNode(Anaphor(), ("x",), True), Reason.OUT_OF_SCOPE),
        (DeleteNode(Alineas((1, 2, 3))), Reason.OUT_OF_SCOPE),  # tous les alinéas
    ],
)
def test_plan_refuses(operation, reason):
    with pytest.raises(Refusal) as refusal:
        plan(operation, LINES)
    assert refusal.value.reason is reason


def test_plan_multiple_anchor_across_lines():
    with pytest.raises(Refusal) as refusal:
        plan(Substitute(WholeArticle(), Anchor("a"), "b"), ("a", "a"))
    assert refusal.value.reason is Reason.QUOTE_MULTIPLE


def test_edits_for_refuses_deleting_the_only_alinea():
    with pytest.raises(Refusal) as refusal:
        plan(DeleteNode(Alineas((1,))), ("Un chat.",))
    assert refusal.value.reason is Reason.OUT_OF_SCOPE
    assert refusal.value.detail == "tous les alinéas supprimés : supprimer l'article"


def test_word_operations_splice_only_the_characters_they_change():
    """Le patch d'une opération sur des mots porte sur les caractères modifiés, pas sur l'alinéa."""
    patch = plan(Substitute(Alineas((1,)), Anchor("chat"), "rat"), LINES)
    assert patch == (Splice.on_chars("5", 0, 3, 5, "r"),)
    patch = plan(InsertEdge(Alineas((2,)), "noirs", False), LINES)
    assert patch == (Splice.on_chars("5", 1, 11, 11, " noirs"),)
