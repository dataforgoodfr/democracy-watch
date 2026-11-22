"""Lecture d'un dispositif : des lignes normalisées aux opérations, avec leur trace.

Une unité d'instruction est lue d'abord comme phrase « en ligne » (citations comprises), puis
comme chapeau de bloc suivi des alinéas cités. Tout ce que la grammaire ne reconnaît pas, ou qu'elle
reconnaît de deux façons différentes, est refusé : jamais de meilleure hypothèse.

Les anaphores (« cet alinéa ») et renvois (« la même substitution ») sont lus ici comme cible
`Anaphor` ou comme `Replay` ; `bind` les résout ensuite avec l'instruction précédente.
"""

from lark import Transformer
from lark.exceptions import UnexpectedInput, VisitError

from engine.domain.operation import Operation
from engine.domain.refusal import Reason, Refusal
from engine.domain.trace import Instruction
from engine.reading.bind import Replay, bind
from engine.reading.blocks import BlockRules
from engine.reading.grammar import parser
from engine.reading.inline import InlineRules
from engine.reading.splitting import block_citations, split_units


class ToOperations(InlineRules, BlockRules, Transformer):
    """Transforme un arbre Lark en opération ; une règle sans méthode est hors périmètre."""

    def __init__(self, body: tuple[str, ...], is_last: bool):
        super().__init__()
        self._body = body
        self._is_last = is_last

    def __default__(self, data, children, meta):
        raise Refusal(Reason.OUT_OF_SCOPE, str(data))

    def _ambig(self, alternatives):
        """Deux analyses identiques une fois transformées ne sont pas une ambiguïté."""
        if any(alternative != alternatives[0] for alternative in alternatives):
            raise Refusal(Reason.AMBIGUOUS, "plusieurs analyses")
        return alternatives[0]


def _transform(tree, body: tuple[str, ...], is_last: bool) -> Operation | Replay:
    """Applique le Transformer en rendant les `Refusal` levés dans ses méthodes."""
    try:
        return ToOperations(body, is_last).transform(tree)
    except VisitError as error:
        raise error.orig_exc from None


def _operation(unit: tuple[str, ...], is_last: bool) -> Operation | Replay:
    """Opération (ou renvoi) d'une unité : phrase en ligne, sinon chapeau de bloc ; lève `Refusal`.

    La cible peut être `Anaphor` : `bind` la résout avec les autres unités.
    """
    try:
        tree = parser().parse("\n".join(unit), start="en_ligne")
    except UnexpectedInput:
        pass
    else:
        return _transform(tree, (), is_last)
    try:
        tree = parser().parse(" ".join(unit[:1]), start="bloc")
    except UnexpectedInput:
        raise Refusal(Reason.OUT_OF_SCOPE, "hors grammaire") from None
    return _transform(tree, block_citations(unit[1:]), is_last)


def read(lines: tuple[str, ...]) -> tuple[Instruction, ...]:
    """Instructions du dispositif, chacune avec son opération ou sa raison de refus.

    Les lignes sont déjà normalisées. Ne lève jamais `Refusal` : un dispositif qu'on ne sait pas
    découper donne une seule instruction refusée.
    """
    try:
        units = split_units(lines)
    except Refusal as refusal:
        return (Instruction(" ".join(lines), reason=refusal.reason, detail=refusal.detail),)
    entries: list[Operation | Replay | Refusal] = []
    for index, unit in enumerate(units):
        try:
            entries.append(_operation(unit, index == len(units) - 1))
        except Refusal as refusal:
            entries.append(refusal)
    instructions = []
    for unit, entry in zip(units, bind(entries), strict=True):
        text = " ".join(unit)
        if isinstance(entry, Refusal):
            instructions.append(Instruction(text, reason=entry.reason, detail=entry.detail))
        else:
            instructions.append(Instruction(text, entry))
    return tuple(instructions)
