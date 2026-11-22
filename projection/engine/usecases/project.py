"""Projection d'un amendement sur un article.

Fonction pure : mêmes entrées, même sortie, aucun I/O. Le résultat est exact ou absent : une
instruction refusée, ou en conflit, refuse tout l'amendement (tout ou rien).
"""

from engine.domain.documents import Amendment, Text
from engine.domain.grafting import graft
from engine.domain.patch import apply, deletes_article
from engine.domain.trace import Projection, Result
from engine.reading import GRAMMAR_VERSION
from engine.usecases.draft import Draft, draft
from engine.usecases.merge import ConflictPolicy, reject_conflicts


def decide(draft: Draft) -> Projection:
    """Projection d'un brouillon dont les conflits sont réglés : appliqué, ou refusé."""
    reason, detail = None, ""
    if draft.refusal is not None:
        reason, detail = draft.refusal.reason, draft.refusal.detail
    else:
        refused = next((i for i in draft.instructions if i.reason is not None), None)
        if refused is not None:
            reason, detail = refused.reason, refused.detail
    args = (draft.amendment.number, draft.number)
    trace = (draft.instructions, GRAMMAR_VERSION, draft.base, draft.amendment.decided_at)
    if reason is not None or draft.article is None:
        return Projection(*args, None, reason, detail, *trace)
    patch = draft.patch
    assert draft.tree is not None
    result = Result(
        draft.article.number,
        apply(draft.article.lines, patch),
        deletes_article(patch),
        graft(draft.tree, patch, draft.text_uid).paragraphs,
    )
    return Projection(*args, result, None, "", *trace)


def project(
    text: Text, amendment: Amendment, on_conflict: ConflictPolicy = reject_conflicts
) -> Projection:
    """Projette `amendment` sur son article dans `text` : texte résultant, ou refus tracé."""
    drafted = draft(text, amendment)
    if drafted.refusal is None:
        (drafted,) = on_conflict([drafted])
    return decide(drafted)
