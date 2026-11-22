"""Cas d'usage : empreinte de base, immutabilité des brouillons, politique de conflit."""

import dataclasses

from engine import usecases
from engine.domain.documents import Amendment, Article, Text
from engine.domain.refusal import Reason, Refusal
from engine.domain.trace import fingerprint
from engine.usecases.draft import draft
from engine.usecases.merge import reject_conflicts

LINES = ("Le premier alinéa.", "Le deuxième alinéa.")
TEXT = Text("PION1", (Article("3", LINES),))


def amendment(*paragraphs, number="CE1"):
    return Amendment(number, "ART. 3", "".join(f"<p>{p}</p>" for p in paragraphs))


DELETE_1 = amendment("Supprimer l’alinéa 1.")
DELETE_2 = amendment("Supprimer l’alinéa 2.", number="CE2")
DELETE_ARTICLE = amendment("Supprimer cet article.", number="CE3")


def test_projection_carries_the_fingerprint_of_its_base():
    base = fingerprint("PION1", Article("3", LINES))
    assert usecases.project(TEXT, DELETE_1).base == base
    assert usecases.project(TEXT, DELETE_2).base == base  # même base, autre amendement
    assert usecases.project(TEXT, DELETE_1).base != usecases.project(
        Text("PION1", (Article("3", LINES[:1]),)), DELETE_1
    )
    assert usecases.project(Text("AUTRE", TEXT.articles), DELETE_1).base != base


def test_projection_of_an_unknown_article_has_no_base():
    projection = usecases.project(TEXT, Amendment("CE1", "ART. 9", "<p>Supprimer cet article.</p>"))
    assert projection.reason is Reason.UNRESOLVED_ARTICLE and projection.base is None


def test_drafts_are_immutable_values():
    original = draft(TEXT, DELETE_1)
    assert original.applicable
    refused = original.with_refusals({0: Refusal(Reason.CONFLICT)})
    assert original.applicable and not refused.applicable
    assert dataclasses.is_dataclass(original) and original.instructions[0].reason is None
    assert not original.refused(Refusal(Reason.AMBIGUOUS)).applicable


def test_reject_conflicts_returns_new_drafts_and_leaves_its_input():
    drafts = [draft(TEXT, DELETE_1), draft(TEXT, DELETE_ARTICLE)]
    merged = reject_conflicts(drafts)
    assert [d.applicable for d in drafts] == [True, True]
    assert [d.applicable for d in merged] == [False, False]
    assert merged[0].instructions[0].reason is Reason.CONFLICT
