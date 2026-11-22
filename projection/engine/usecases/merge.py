"""Fusion des brouillons d'un même article : conflits entre instructions, article vidé.

Une politique de conflit est une fonction `brouillons → brouillons` : elle rend de nouveaux
brouillons dont les instructions en conflit sont refusées. `reject_conflicts` est la politique v1 :
tout amendement concerné par un conflit est refusé, jamais de départage.
"""

import itertools
from collections.abc import Callable, Sequence

from engine.domain.patch import apply, conflicts, deletes_article
from engine.domain.refusal import Reason, Refusal
from engine.usecases.draft import Draft

ConflictPolicy = Callable[[Sequence[Draft]], tuple[Draft, ...]]

_CONFLICT = Refusal(Reason.CONFLICT, "cibles non disjointes")
_EMPTIED = Refusal(Reason.OUT_OF_SCOPE, "tous les alinéas supprimés : supprimer l'article")


def reject_conflicts(drafts: Sequence[Draft]) -> tuple[Draft, ...]:
    """Refuse les instructions qui ne peuvent pas s'appliquer ensemble.

    Les brouillons visent tous le même article. Les patchs de toutes les instructions sont
    comparés deux à deux : cibles non disjointes → `CONFLICT`. Si tout le reste est applicable
    mais que la composition vide l'article sans le supprimer, les instructions qui ont un patch
    sont refusées `OUT_OF_SCOPE`.
    """
    slots = [(i, k) for i, draft in enumerate(drafts) for k in range(len(draft.instructions))]
    refusals: dict[tuple[int, int], Refusal] = {}
    for (i, k), (j, m) in itertools.combinations(slots, 2):
        if any(conflicts(a, b) for a in drafts[i].patches[k] for b in drafts[j].patches[m]):
            refusals[i, k] = refusals[j, m] = _CONFLICT
    merged = tuple(
        draft.with_refusals({k: r for (i, k), r in refusals.items() if i == index})
        for index, draft in enumerate(drafts)
    )
    if not all(draft.applicable for draft in merged):
        return merged
    patch = tuple(splice for draft in merged for splice in draft.patch)
    first = merged[0].article
    if patch and first is not None and not apply(first.lines, patch) and not deletes_article(patch):
        return tuple(
            draft.with_refusals({k: _EMPTIED for k, p in enumerate(draft.patches) if p})
            for draft in merged
        )
    return merged
