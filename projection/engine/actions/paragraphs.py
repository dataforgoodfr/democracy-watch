"""Opérations sur des alinéas entiers ou l'article : supprimer, rédiger, insérer."""

import dataclasses

from engine.domain.documents import Article
from engine.domain.operation import Retargetable
from engine.domain.patch import Patch, Splice
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Target, WholeArticle, resolve


@dataclasses.dataclass(frozen=True)
class DeleteNode(Retargetable):  # alinéas et article
    target: Target

    def plan(self, article: Article) -> Patch:
        count = len(article.lines)
        indices = resolve(self.target, article.number, count)
        if isinstance(self.target, WholeArticle):
            return (Splice.on_article(article.number, ()),)
        if len(set(indices)) == count:
            raise Refusal(Reason.OUT_OF_SCOPE, "tous les alinéas supprimés : supprimer l'article")
        return tuple(Splice.on_lines(article.number, i, i + 1, ()) for i in indices)


@dataclasses.dataclass(frozen=True)
class Rewrite(Retargetable):  # rewrite, b_rewrite, b_rewrite_compte
    target: Target
    lines: tuple[str, ...]

    def plan(self, article: Article) -> Patch:
        indices = resolve(self.target, article.number, len(article.lines))
        if isinstance(self.target, WholeArticle):
            return (Splice.on_article(article.number, self.lines),)
        if indices != tuple(range(indices[0], indices[-1] + 1)):
            raise Refusal(Reason.OUT_OF_SCOPE, "réécriture d'alinéas non contigus")
        return (Splice.on_lines(article.number, indices[0], indices[-1] + 1, self.lines),)


@dataclasses.dataclass(frozen=True)
class InsertNode(Retargetable):  # b_insert_node, b_insert_debut, b_complete par des alinéas
    """Alinéas insérés après (ou avant) la cible ; article entier : à la fin (ou au début)."""

    target: Target
    lines: tuple[str, ...]
    after: bool

    def plan(self, article: Article) -> Patch:
        indices = resolve(self.target, article.number, len(article.lines))
        if isinstance(self.target, WholeArticle):
            point = len(article.lines) if self.after else 0
        elif len(indices) == 1:
            point = indices[0] + 1 if self.after else indices[0]
        else:
            raise Refusal(Reason.OUT_OF_SCOPE, "insertion d'alinéas relative à plusieurs alinéas")
        return (Splice.on_lines(article.number, point, point, self.lines),)
