"""Rendu en graphe d'une consolidation."""

from engine.adapters.graph import render
from engine.domain.documents import Amendment, Article, Text
from engine.usecases import consolidate

TEXT = Text(
    "PION1", (Article("3", ("Le premier alinéa.", "Le deuxième alinéa.", "Le troisième alinéa.")),)
)


def amendment(body, number):
    return Amendment(number, "ART. 3", f"<p>{body}</p>")


def test_single_amendment_is_a_linear_history():
    graph = render(consolidate(TEXT, [amendment("Supprimer l’alinéa 1.", "CE1")]))
    lines = graph.splitlines()
    assert lines[0] == "* base  article 3"
    assert lines[1].startswith("* ") and "(CE1)" in lines[1]
    assert lines[-1] == "*  résultat · 2 alinéa(s)"


def test_disjoint_amendments_fork_and_merge():
    graph = render(
        consolidate(
            TEXT,
            [amendment("Supprimer l’alinéa 1.", "CE1"), amendment("Supprimer l’alinéa 2.", "CE2")],
        )
    )
    lines = graph.splitlines()
    assert lines[1] == "|\\"
    assert lines[2].startswith("* |") and lines[3].startswith("| *")
    assert lines[4] == "|/"
    assert lines[-1] == "*  résultat · 1 alinéa(s)"


def test_conflict_is_marked_and_blocks_the_result():
    graph = render(
        consolidate(
            TEXT,
            [amendment("Supprimer l’alinéa 1.", "CE1"), amendment("Supprimer l’alinéa 1.", "CE2")],
        )
    )
    assert "x" in graph and "conflit" in graph
    assert graph.splitlines()[-1].startswith("o  non consolidé")


def test_amendment_without_article_is_listed_apart():
    other = Amendment("CE9", "ART. 3 À 5", "<p>Supprimer l’alinéa 1.</p>")
    assert "hors article" in render(consolidate(TEXT, [other]))
