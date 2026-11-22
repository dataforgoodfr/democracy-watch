"""Règles de l'analyse d'une phrase « en ligne » : désignations, préfixes, actions.

`InlineRules` est mélangé au Transformer Lark de `reading.reader` : chaque méthode porte le nom
d'une règle de `grammaires/`.
"""

import dataclasses
from collections.abc import Callable

from lark import Token

from engine.actions import (
    DeleteEnd,
    DeleteNode,
    DeleteWords,
    InsertEdge,
    InsertWords,
    Rewrite,
    RewriteEnd,
    Substitute,
)
from engine.domain.normalization import article_number
from engine.domain.operation import Operation
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, Anaphor, Target, WholeArticle
from engine.domain.writing import Anchor
from engine.reading.bind import Replay
from engine.reading.ordinals import ORDINALS


@dataclasses.dataclass(frozen=True)
class _Prefix:
    """Préfixe d'une phrase en ligne : cible éventuelle ; `start` : début (True) ou fin (False)."""

    target: Target | None
    start: bool | None = None


@dataclasses.dataclass(frozen=True)
class _Action:
    """Action d'une phrase en ligne, en attente de sa cible.

    `kind(target, *args)` construit l'opération (comparable, contrairement à une lambda) ;
    `own` : désignation propre à l'action ; `edge` : l'action exige un préfixe début/fin et
    reçoit alors `start` en dernier argument.
    """

    kind: Callable[..., Operation | Replay]
    args: tuple = ()
    own: Target | None = None
    edge: bool = False


def _merge_target(prefix: Target | None, own: Target | None) -> Target:
    """Cible unique d'une phrase : le préfixe et la désignation de l'action doivent s'accorder.

    Une cible concrète l'emporte sur une anaphore de la même phrase ; une anaphore seule est
    rendue telle quelle (`Anaphor`) pour que `bind` la résolve.
    """
    designated = [target for target in (prefix, own) if target is not None]
    concrete = {target for target in designated if not isinstance(target, Anaphor)}
    if len(concrete) > 1:
        raise Refusal(Reason.AMBIGUOUS, "deux cibles")
    if concrete:
        return concrete.pop()
    if designated:
        return Anaphor()  # antécédent résolu ensuite par bind
    raise Refusal(Reason.TARGET_NOT_FOUND, "aucune cible")


def _anchor(children: list) -> tuple[Anchor, list]:
    """Retire de tête l'ancre (rang éventuel, puis citation) et rend le reste."""
    occurrence = children.pop(0) if isinstance(children[0], int) else None
    return Anchor(children.pop(0), occurrence), children


class InlineRules:
    """Règles des phrases en ligne : terminaux, désignations, préfixes, actions."""

    # ---- terminaux

    def APRES(self, token: Token) -> bool:
        return token.lower() == "après"

    def CITATION(self, token: Token) -> str:
        if token == "«»":
            raise Refusal(Reason.OUT_OF_SCOPE, "citation vide")
        if "\n" in token:
            raise Refusal(Reason.INCONSISTENT_BLOCK, "citation sur plusieurs lignes")
        return token[1:-1]

    def SUBDIVISION(self, token: Token):
        raise Refusal(Reason.OUT_OF_SCOPE, "subdivision")

    # ---- désignations

    def alinea_numero(self, children):
        return Alineas((int(children[0]),))

    def alinea_ordinal(self, children):
        return Alineas((ORDINALS[children[0].lower()],))

    def alineas_de_a(self, children):
        first, last = int(children[0]), int(children[1])
        if first > last:
            raise Refusal(Reason.TARGET_NOT_FOUND, f"plage inversée {first} à {last}")
        return Alineas(tuple(range(first, last + 1)))

    def alineas_liste(self, children):
        return Alineas(tuple(int(number) for number in children))

    def cet_alinea(self, children):
        return Anaphor()

    def meme_alinea(self, children):
        if children:
            raise Refusal(Reason.AMBIGUOUS, f"« même alinéa {children[0]} » : numéro et renvoi")
        return Anaphor()

    def cet_article(self, children):
        return WholeArticle()

    def article_numero(self, children):
        return WholeArticle(article_number(children[0]))

    def occurrence(self, children):
        return ORDINALS[children[0].lower()]

    # ---- préfixes

    def dans(self, children):
        return _Prefix(children[0])

    def fin_de(self, children):
        return _Prefix(next(iter(children), None), start=False)

    def debut_de(self, children):
        return _Prefix(next(iter(children), None), start=True)

    # ---- actions en ligne

    def substitute(self, children):
        anchor, (new,) = _anchor(children)
        return _Action(Substitute, (anchor, new))

    def delete_mots(self, children):
        anchor, _ = _anchor(children)
        return _Action(DeleteWords, (anchor,))

    def insert_mots(self, children):
        after, *rest = children
        anchor, (new,) = _anchor(rest)
        return _Action(InsertWords, (anchor, new, after))

    def rewrite_fin(self, children):
        after, *rest = children
        anchor, (*own, new) = _anchor(rest)
        if not after:
            raise Refusal(Reason.OUT_OF_SCOPE, "avant … rédiger ainsi la fin")
        return _Action(RewriteEnd, (anchor, new), next(iter(own), None))

    def delete_fin(self, children):
        after, *rest = children
        anchor, own = _anchor(rest)
        if not after:
            raise Refusal(Reason.OUT_OF_SCOPE, "avant … supprimer la fin")
        return _Action(DeleteEnd, (anchor,), next(iter(own), None))

    def insert_bord(self, children):
        (new,) = children
        return _Action(InsertEdge, (new,), edge=True)

    def complete(self, children):
        own, new = children
        return _Action(InsertEdge, (new, False), own)

    def delete_node(self, children):
        return _Action(DeleteNode, (), children[0])

    def rewrite(self, children):
        own, new = children
        return _Action(Rewrite, ((new,),), own)

    def renvoi(self, children):
        genre, *trailing = children
        if trailing and trailing[0].start is not None:
            raise Refusal(Reason.OUT_OF_SCOPE, "renvoi : préfixe début/fin")
        return _Action(Replay, (str(genre).lower(),), trailing[0].target if trailing else None)

    def en_ligne(self, children):
        *head, action = children
        prefix = head[0] if head else _Prefix(None)
        if action.edge and prefix.start is None:
            raise Refusal(Reason.OUT_OF_SCOPE, "insertion hors début ou fin d'alinéa")
        if prefix.start is not None and not action.edge:
            raise Refusal(Reason.OUT_OF_SCOPE, "préfixe début/fin ignoré par l'action")
        target = _merge_target(prefix.target, action.own)
        return action.kind(target, *action.args, *((prefix.start,) if action.edge else ()))
