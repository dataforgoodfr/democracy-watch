"""Règles de l'analyse d'un bloc cité : chapeau suivi des alinéas cités."""

from engine.actions import InsertEdge, InsertNode, Rewrite
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, WholeArticle
from engine.reading.ordinals import CARDINALS


class BlockRules:
    """Règles des blocs, mélangées au Transformer Lark de `reading.reader`.

    `_body` : les alinéas cités du bloc ; `_is_last` : le bloc est la dernière instruction.
    """

    _body: tuple[str, ...]
    _is_last: bool

    # ---- comptes de bloc : nombre d'alinéas annoncé (None : « les alinéas suivants »)

    def un_alinea(self, children):
        return 1

    def n_alineas(self, children):
        number = children[0].lower()
        return int(number) if number.isdigit() else CARDINALS[number]

    def alineas_sans_nombre(self, children):
        return None

    def _lines(self, count: int | None) -> tuple[str, ...]:
        """Alinéas du bloc, si leur nombre est celui que le chapeau annonce."""
        if count is None:
            if not self._is_last:
                raise Refusal(Reason.INCONSISTENT_BLOCK, "« les alinéas suivants » sans nombre")
        elif count != len(self._body):
            raise Refusal(
                Reason.INCONSISTENT_BLOCK, f"{count} alinéas annoncés, {len(self._body)} cités"
            )
        return self._body

    # ---- blocs

    def b_rewrite(self, children):
        return Rewrite(children[0], self._body)

    def b_rewrite_compte(self, children):
        target, count = children
        return Rewrite(target, self._lines(count))

    def b_insert_node(self, children):
        after, target, count = children
        if (
            isinstance(target, Alineas)
            and len(target.positions) != 1
            or isinstance(target, WholeArticle)
        ):
            raise Refusal(Reason.OUT_OF_SCOPE, "insertion hors d'un alinéa précis")
        return InsertNode(target, self._lines(count), after)

    def b_insert_debut(self, children):
        *designated, count = children
        if not designated:
            raise Refusal(Reason.TARGET_NOT_FOUND, "aucune cible")
        if not isinstance(designated[0], WholeArticle):
            raise Refusal(Reason.OUT_OF_SCOPE, "début hors de l'article")
        return InsertNode(designated[0], self._lines(count), False)

    def b_complete(self, children):
        target, *count = children
        if count:
            if not isinstance(target, WholeArticle):
                raise Refusal(Reason.OUT_OF_SCOPE, "alinéas ajoutés hors de l'article")
            return InsertNode(target, self._lines(count[0]), True)
        if len(self._body) != 1:
            raise Refusal(Reason.INCONSISTENT_BLOCK, "compléter par des mots : un seul alinéa")
        return InsertEdge(target, self._body[0], False)
