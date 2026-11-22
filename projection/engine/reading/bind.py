"""Contexte intra-dispositif : anaphores et renvois résolus par l'instruction précédente.

`bind` reçoit, dans l'ordre du dispositif, ce que l'analyse a lu de chaque unité : une opération
(éventuellement à cible `Anaphor`), un `Replay` (renvoi « Procéder à la même substitution… ») ou un
`Refusal`. Il rend pour chaque unité une opération sans `Anaphor`, ou un `Refusal`, en une passe et
sans lever d'exception.

Seule l'instruction IMMÉDIATEMENT précédente sert d'antécédent, une fois elle-même résolue (les
chaînes de renvois ou d'anaphores marchent). Si elle est absente ou refusée, ou si elle ne désigne
pas exactement un alinéa, on refuse : jamais de meilleure hypothèse.

Les positions sont celles du texte d'entrée (application parallèle) : la même position désigne le
même alinéa, quelles que soient les instructions intermédiaires.

Deux instructions sur le même alinéa se heurtent ensuite à `patch.conflicts` (même alinéa =
conflit tant que les opérations remplacent l'alinéa entier) ; seule une insertion de bloc « Après
le même alinéa » (point d'insertion au bord de l'alinéa) n'en est pas un.
"""

import dataclasses

from engine.actions import DeleteNode, DeleteWords, InsertNode, InsertWords, Substitute
from engine.domain.operation import Operation
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, Anaphor, Target


@dataclasses.dataclass(frozen=True)
class Replay:
    """Renvoi : rejouer l'opération précédente de ce `genre` sur une nouvelle `target`.

    `genre` : « substitution », « suppression » ou « insertion » (minuscules). Champs dans l'ordre
    `(target, genre)` : `Replay` sert ainsi d'action `kind(target, *args)` à l'analyse.
    """

    target: Target
    genre: str


def _retarget(operation: Operation, target: Target) -> Operation:
    """La même opération sur une autre cible (les opérations sont des dataclasses immuables)."""
    if not dataclasses.is_dataclass(operation) or isinstance(operation, type):
        raise TypeError(f"{operation!r} n'est pas une opération (dataclass)")
    return dataclasses.replace(operation, target=target)


# Opérations rejouables par genre de renvoi.
_REPLAYABLE = {
    "substitution": (Substitute,),
    "suppression": (DeleteWords, DeleteNode),
    "insertion": (InsertWords,),
}


def _single_position(previous: Operation | Refusal | None) -> Alineas:
    """Cible de l'instruction précédente, si c'est un seul alinéa (antécédent d'une anaphore).

    Une insertion d'alinéa est refusée : « cet alinéa » pourrait désigner l'alinéa inséré, que les
    positions du texte d'entrée ne savent pas nommer.
    """
    if previous is None:
        raise Refusal(Reason.TARGET_NOT_FOUND, "antécédent absent : aucune instruction précédente")
    if isinstance(previous, Refusal):
        raise Refusal(Reason.TARGET_NOT_FOUND, "antécédent : l'instruction précédente est refusée")
    target = previous.target
    if not isinstance(target, Alineas) or len(target.positions) != 1:
        raise Refusal(
            Reason.TARGET_NOT_FOUND,
            "antécédent : l'instruction précédente ne vise pas un seul alinéa",
        )
    if isinstance(previous, InsertNode):
        raise Refusal(
            Reason.AMBIGUOUS,
            "antécédent : l'instruction précédente insère un alinéa (l'ancien ou le nouveau ?)",
        )
    return target


def _replay(replay: Replay, previous: Operation | Refusal | None) -> Operation:
    """Rejoue `previous` sur la cible du renvoi, si elle est d'un genre compatible."""
    if not isinstance(replay.target, Alineas):
        raise Refusal(Reason.OUT_OF_SCOPE, "renvoi : seule une cible en alinéas est admise")
    if previous is None:
        raise Refusal(Reason.TARGET_NOT_FOUND, "renvoi : aucune instruction précédente")
    if isinstance(previous, Refusal):
        raise Refusal(Reason.TARGET_NOT_FOUND, "renvoi : l'instruction précédente est refusée")
    if not isinstance(previous, _REPLAYABLE[replay.genre]):
        raise Refusal(
            Reason.AMBIGUOUS, f"renvoi : la même {replay.genre} d'une autre sorte d'opération"
        )
    if isinstance(previous, DeleteNode) and not isinstance(previous.target, Alineas):
        raise Refusal(Reason.OUT_OF_SCOPE, "renvoi : suppression de l'article")
    return _retarget(previous, replay.target)


def _resolve(
    entry: Operation | Replay | Refusal, previous: Operation | Refusal | None
) -> Operation | Refusal:
    if isinstance(entry, Refusal):
        return entry
    try:
        if isinstance(entry, Replay):
            return _replay(entry, previous)
        if isinstance(entry.target, Anaphor):
            return _retarget(entry, _single_position(previous))
    except Refusal as refusal:
        return refusal
    return entry


def bind(entries: list[Operation | Replay | Refusal]) -> list[Operation | Refusal]:
    """Résout anaphores et renvois ; ne lève jamais `Refusal` (les refus sont rendus en valeur)."""
    bound: list[Operation | Refusal] = []
    for entry in entries:
        bound.append(_resolve(entry, bound[-1] if bound else None))
    return bound
