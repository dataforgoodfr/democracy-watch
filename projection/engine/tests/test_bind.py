"""Tests de `bind` : anaphores et renvois."""

import dataclasses

import pytest

from engine.actions import (
    DeleteNode,
    DeleteWords,
    InsertEdge,
    InsertNode,
    InsertWords,
    Rewrite,
    RewriteEnd,
    Substitute,
)
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, Anaphor, WholeArticle
from engine.domain.writing import Anchor
from engine.reading.bind import Replay, bind

AL2 = Alineas((2,))
AL5 = Alineas((5,))
A = Anchor("a")
SUBSTITUTE = Substitute(AL2, A, "b")
DELETE_MOTS = DeleteWords(AL2, A)
INSERT_MOTS = InsertWords(AL2, A, "b", True)


def refused(reason, detail=""):
    return Refusal(reason, detail)


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        pytest.param(
            [DELETE_MOTS, DeleteNode(Anaphor())], [DELETE_MOTS, DeleteNode(AL2)], id="anaphor"
        ),
        pytest.param(
            [DeleteWords(Alineas((-1,)), A), Rewrite(Anaphor(), ("y",))],
            [DeleteWords(Alineas((-1,)), A), Rewrite(Alineas((-1,)), ("y",))],
            id="anaphor_negative_position",
        ),
        pytest.param(
            [DELETE_MOTS, DeleteNode(Anaphor()), DeleteNode(Anaphor())],
            [DELETE_MOTS, DeleteNode(AL2), DeleteNode(AL2)],
            id="anaphor_chain",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(AL5, "substitution")],
            [SUBSTITUTE, Substitute(AL5, A, "b")],
            id="replay_substitute",
        ),
        pytest.param(
            [DELETE_MOTS, Replay(AL5, "suppression")],
            [DELETE_MOTS, DeleteWords(AL5, A)],
            id="replay_delete_mots",
        ),
        pytest.param(
            [DeleteNode(AL2), Replay(Alineas((5, 6)), "suppression")],
            [DeleteNode(AL2), DeleteNode(Alineas((5, 6)))],
            id="replay_delete_node",
        ),
        pytest.param(
            [INSERT_MOTS, Replay(AL5, "insertion")],
            [INSERT_MOTS, InsertWords(AL5, A, "b", True)],
            id="replay_insert",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(AL5, "substitution"), Replay(Alineas((7,)), "substitution")],
            [SUBSTITUTE, Substitute(AL5, A, "b"), Substitute(Alineas((7,)), A, "b")],
            id="replay_chain",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(AL5, "substitution"), DeleteNode(Anaphor())],
            [SUBSTITUTE, Substitute(AL5, A, "b"), DeleteNode(AL5)],
            id="anaphor_after_replay",
        ),
        pytest.param(
            [DELETE_MOTS, Replay(AL5, "suppression"), DeleteNode(Anaphor())],
            [DELETE_MOTS, DeleteWords(AL5, A), DeleteNode(AL5)],
            id="anaphor_after_valid_replay",
        ),
        pytest.param(
            [DELETE_MOTS, DeleteNode(AL5), DeleteNode(Anaphor())],
            [DELETE_MOTS, DeleteNode(AL5), DeleteNode(AL5)],
            id="anaphor_targets_immediately_previous",
        ),
        pytest.param(
            [INSERT_MOTS, Replay(Alineas((5, 6)), "insertion")],
            [INSERT_MOTS, InsertWords(Alineas((5, 6)), A, "b", True)],
            id="replay_insert_several_alineas",
        ),
        pytest.param([], [], id="empty"),
    ],
)
def test_bind_resolves(entries, expected):
    bound = bind(entries)
    assert bound == expected
    assert all(not isinstance(op, Refusal) and op.target != Anaphor() for op in bound)


@pytest.mark.parametrize(
    ("entries", "reason", "detail"),
    [
        pytest.param(
            [DeleteNode(Anaphor())],
            Reason.TARGET_NOT_FOUND,
            "antécédent absent",
            id="no_antecedent",
        ),
        pytest.param(
            [DeleteWords(Alineas((2, 3)), A), DeleteNode(Anaphor())],
            Reason.TARGET_NOT_FOUND,
            "un seul alinéa",
            id="several_alineas",
        ),
        pytest.param(
            [DeleteNode(WholeArticle()), DeleteNode(Anaphor())],
            Reason.TARGET_NOT_FOUND,
            "un seul alinéa",
            id="whole_article",
        ),
        pytest.param(
            [refused(Reason.AMBIGUOUS), DeleteNode(Anaphor())],
            Reason.TARGET_NOT_FOUND,
            "précédente est refusée",
            id="previous_refused",
        ),
        pytest.param(
            [InsertNode(AL2, ("x",), True), DeleteNode(Anaphor())],
            Reason.AMBIGUOUS,
            "insère un alinéa",
            id="anaphor_after_insert_node",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(AL5, "suppression")],
            Reason.AMBIGUOUS,
            "autre sorte d'opération",
            id="incompatible_genre",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(AL5, "insertion")],
            Reason.AMBIGUOUS,
            "autre sorte d'opération",
            id="incompatible_insertion",
        ),
        pytest.param(
            [DeleteNode(WholeArticle()), Replay(AL5, "suppression")],
            Reason.OUT_OF_SCOPE,
            "suppression de l'article",
            id="replay_of_article_deletion",
        ),
        pytest.param(
            [Replay(AL5, "substitution")],
            Reason.TARGET_NOT_FOUND,
            "aucune instruction précédente",
            id="replay_without_antecedent",
        ),
        pytest.param(
            [refused(Reason.AMBIGUOUS), Replay(AL5, "substitution")],
            Reason.TARGET_NOT_FOUND,
            "précédente est refusée",
            id="replay_after_refusal",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(Anaphor(), "substitution")],
            Reason.OUT_OF_SCOPE,
            "cible en alinéas",
            id="replay_on_anaphor",
        ),
        pytest.param(
            [SUBSTITUTE, Replay(WholeArticle(), "substitution")],
            Reason.OUT_OF_SCOPE,
            "cible en alinéas",
            id="replay_on_article",
        ),
    ],
)
def test_bind_refuses(entries, reason, detail):
    bound = bind(entries)[-1]
    assert isinstance(bound, Refusal)
    assert bound.reason is reason
    assert detail in bound.detail


def test_bind_keeps_refusals_and_never_raises():
    original = refused(Reason.OUT_OF_SCOPE, "x")
    assert bind([original, SUBSTITUTE]) == [original, SUBSTITUTE]


_OPERATIONS = {
    "DeleteWords": DELETE_MOTS,
    "InsertWords": INSERT_MOTS,
    "Substitute": SUBSTITUTE,
    "InsertNode": InsertNode(AL2, ("x",), True),
    "Rewrite": Rewrite(AL2, ("x",)),
    "RewriteEnd": RewriteEnd(AL2, A, "b"),
    "InsertEdge": InsertEdge(AL2, "b", True),
}
_REPLAY_PAIRS = [
    ("substitution", "Substitute"),
    ("suppression", "DeleteWords"),
    ("suppression", "DeleteNode"),
    ("insertion", "InsertWords"),
]


@pytest.mark.parametrize(
    ("genre", "name"),
    [
        (genre, name)
        for genre in ("substitution", "suppression", "insertion")
        for name in _OPERATIONS
        if (genre, name) not in _REPLAY_PAIRS
    ],
)
def test_replay_matrix_refuses_other_kinds(genre, name):
    """Un renvoi d'un genre ne rejoue que les opérations de ce genre (`_REPLAYABLE`)."""
    refusal = bind([_OPERATIONS[name], Replay(AL5, genre)])[-1]
    assert isinstance(refusal, Refusal)
    assert refusal.reason is Reason.AMBIGUOUS
    assert "autre sorte d'opération" in refusal.detail


@pytest.mark.parametrize(("genre", "name"), _REPLAY_PAIRS)
def test_replay_matrix_resolves_valid_pairs(genre, name):
    previous = DeleteNode(AL2) if name == "DeleteNode" else _OPERATIONS[name]
    bound = bind([previous, Replay(AL5, genre)])[-1]
    assert bound == dataclasses.replace(previous, target=AL5)
