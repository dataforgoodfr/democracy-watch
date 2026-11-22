"""Statut d'un amendement : lecture métier, dérivée de la raison de refus.

Le statut ne remplace jamais `Reason` : il en est déduit (`status_of`), ou imposé par la
consolidation quand elle sait mieux (série identique, sous-amendement).

Seuls les statuts des amendements adoptés sont implémentés. Les statuts du RFC `predicted_fallen`,
`predicted_alive`, `undetermined` et `ignored` sont reportés : ils supposent le sort de
l'amendement, que le moteur ne reçoit pas encore.
"""

import enum
from typing import Any

from engine.domain.refusal import Reason


class Status(enum.StrEnum):
    """Statut d'un amendement adopté."""

    APPLIED = "applied"
    IDENTICAL = "identical"
    SUB_AMENDMENT = "sub_amendment"
    NOT_PARSED = "not_parsed"
    PENDING = "pending"
    AMBIGUOUS = "ambiguous"


STATUS_OF_REASON: dict[Reason, Status] = {
    Reason.AMBIGUOUS: Status.AMBIGUOUS,
    Reason.QUOTE_MULTIPLE: Status.AMBIGUOUS,
    Reason.TARGET_NOT_FOUND: Status.PENDING,
    Reason.TARGET_GONE: Status.PENDING,
    Reason.QUOTE_MISSING: Status.PENDING,
    Reason.UNRESOLVED_ARTICLE: Status.PENDING,
    Reason.INCONSISTENT_BLOCK: Status.PENDING,
    Reason.CONFLICT: Status.PENDING,
    Reason.OUT_OF_SCOPE: Status.NOT_PARSED,
}


def status_of(reason: Reason | None, result: Any) -> Status:
    """Statut déduit : appliqué si un résultat et pas de refus, sinon selon la raison."""
    if reason is None:
        if result is None:
            raise ValueError("ni résultat ni raison de refus")
        return Status.APPLIED
    return STATUS_OF_REASON[reason]
