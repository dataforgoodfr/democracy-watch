"""Fusion des brouillons d'un même article : conflits entre instructions, article vidé.

Une politique de conflit est une fonction `brouillons → brouillons` : elle rend de nouveaux
brouillons dont les instructions en conflit sont refusées. `reject_conflicts` refuse tous les
amendements en conflit ; `oldest_wins` (défaut) garde celui dont la décision est la plus ancienne.
"""

import itertools
from collections.abc import Callable, Sequence

from engine.domain.patch import apply, conflicts, deletes_article
from engine.domain.refusal import Reason, Refusal
from engine.usecases.draft import Draft

ConflictPolicy = Callable[[Sequence[Draft]], tuple[Draft, ...]]

_CONFLICT = Refusal(Reason.CONFLICT, "cibles non disjointes")
_OLDER = Refusal(Reason.CONFLICT, "cibles non disjointes d'un amendement décidé plus tôt")
_EMPTIED = Refusal(Reason.OUT_OF_SCOPE, "tous les alinéas supprimés : supprimer l'article")


Slot = tuple[int, int]  # (indice du brouillon, indice de l'instruction)


def _slots(drafts: Sequence[Draft]) -> list[Slot]:
    return [(i, k) for i, draft in enumerate(drafts) for k in range(len(draft.instructions))]


def _clash(drafts: Sequence[Draft], a: Slot, b: Slot) -> bool:
    """Vrai si les patchs des deux instructions ne peuvent pas s'appliquer ensemble."""
    return any(
        conflicts(x, y) for x in drafts[a[0]].patches[a[1]] for y in drafts[b[0]].patches[b[1]]
    )


def _all_refused(drafts: Sequence[Draft]) -> dict[Slot, Refusal]:
    """Politique « refuser tout » : chaque instruction en conflit avec une autre est refusée."""
    refusals: dict[Slot, Refusal] = {}
    for a, b in itertools.combinations(_slots(drafts), 2):
        if _clash(drafts, a, b):
            refusals[a] = refusals[b] = _CONFLICT
    return refusals


def _older_kept(drafts: Sequence[Draft]) -> dict[Slot, Refusal]:
    """Politique « le plus ancien gagne » : on parcourt les dates de décision par ordre croissant.

    Une instruction en conflit avec une instruction conservée, plus ancienne, est refusée. Deux
    instructions de même date (ou sans date) en conflit sont toutes deux refusées : pas de
    départage.
    """
    by_date: dict[tuple[bool, str], list[Slot]] = {}
    for slot in _slots(drafts):
        date = drafts[slot[0]].amendment.decided_at
        by_date.setdefault((date is None, date or ""), []).append(slot)
    kept: list[Slot] = []
    refusals: dict[Slot, Refusal] = {}
    for _, group in sorted(by_date.items()):
        for a in group:
            if any(_clash(drafts, a, b) for b in kept):
                refusals[a] = _OLDER
        for a, b in itertools.combinations(group, 2):
            if _clash(drafts, a, b):
                refusals[a] = refusals[b] = _CONFLICT
        kept += [slot for slot in group if slot not in refusals]
    return refusals


def _merge(drafts: Sequence[Draft], refusals: dict[Slot, Refusal]) -> tuple[Draft, ...]:
    """Applique les refus, puis refuse la composition qui vide l'article sans le supprimer.

    Les brouillons visent tous le même article. Si tout le reste est applicable mais que la
    composition vide l'article, les instructions qui ont un patch sont refusées `OUT_OF_SCOPE`.
    """
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


def reject_conflicts(drafts: Sequence[Draft]) -> tuple[Draft, ...]:
    """Refuse toutes les instructions dont les cibles ne sont pas disjointes (`CONFLICT`)."""
    return _merge(drafts, _all_refused(drafts))


def oldest_wins(drafts: Sequence[Draft]) -> tuple[Draft, ...]:
    """En cas de conflit, garde l'instruction dont la date de décision est la plus ancienne."""
    return _merge(drafts, _older_kept(drafts))
