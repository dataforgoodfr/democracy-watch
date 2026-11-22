"""Opérations sur les mots d'un alinéa : substituer, supprimer, insérer, la fin."""

import dataclasses
from collections.abc import Callable

from engine.domain import writing
from engine.domain.documents import Article
from engine.domain.patch import Patch, Splice
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Target, resolve
from engine.domain.writing import Anchor


def _splice_chars(article: str, index: int, old: str, new: str) -> Splice:
    """Le splice, au niveau des caractères, qui change l'alinéa `index` de `old` en `new`."""
    start, end, replacement = writing.changed_span(old, new)
    return Splice.on_chars(article, index, start, end, replacement)


def _rewrite_line(
    article: Article,
    target: Target,
    anchor: Anchor,
    rewrite: Callable[[str, int, int], str],
) -> Patch:
    """Repère l'ancre dans les alinéas visés et réécrit l'alinéa qui la porte.

    Sur une cible de plusieurs alinéas, l'ancre est cherchée dans l'ensemble : présente dans un
    seul, elle est unique et c'est celui-là qui est modifié. `rewrite(texte, début, fin)` rend le
    nouveau texte de l'alinéa.
    """
    indices = resolve(target, article.number, len(article.lines))
    found, start, end = writing.find_anchor([article.lines[i] for i in indices], anchor)
    index = indices[found]
    text = rewrite(article.lines[index], start, end)
    if text == "":
        raise Refusal(Reason.OUT_OF_SCOPE, "alinéa vidé")
    return (_splice_chars(article.number, index, article.lines[index], text),)


@dataclasses.dataclass(frozen=True)
class Substitute:
    target: Target
    anchor: Anchor
    new: str

    def plan(self, article: Article) -> Patch:
        return _rewrite_line(
            article,
            self.target,
            self.anchor,
            lambda text, start, end: text[:start] + self.new + text[end:],
        )


@dataclasses.dataclass(frozen=True)
class DeleteWords:
    target: Target
    anchor: Anchor

    def plan(self, article: Article) -> Patch:
        return _rewrite_line(article, self.target, self.anchor, writing.cut)


@dataclasses.dataclass(frozen=True)
class InsertWords:
    target: Target
    anchor: Anchor
    new: str
    after: bool  # « après » (True) ou « avant » (False) l'ancre

    def plan(self, article: Article) -> Patch:
        return _rewrite_line(
            article,
            self.target,
            self.anchor,
            lambda text, start, end: writing.insert_at(
                text, end if self.after else start, self.new
            ),
        )


@dataclasses.dataclass(frozen=True)
class InsertEdge:  # insert_bord, complete, debut_de, b_complete par des mots
    target: Target
    new: str
    start: bool  # début (True) ou fin (False) de l'alinéa

    def plan(self, article: Article) -> Patch:
        indices = resolve(self.target, article.number, len(article.lines))
        if len(indices) != 1:
            raise Refusal(Reason.OUT_OF_SCOPE, "insertion en bord sur plusieurs alinéas")
        index = indices[0]
        old = article.lines[index]
        text = writing.insert_edge(old, self.new, self.start)
        return (_splice_chars(article.number, index, old, text),)


@dataclasses.dataclass(frozen=True)
class RewriteEnd:
    target: Target
    anchor: Anchor
    new: str

    def plan(self, article: Article) -> Patch:
        return _rewrite_line(
            article,
            self.target,
            self.anchor,
            lambda text, _, end: writing.rewrite_after(text, end, self.new),
        )


@dataclasses.dataclass(frozen=True)
class DeleteEnd:
    target: Target
    anchor: Anchor

    def plan(self, article: Article) -> Patch:
        return _rewrite_line(
            article, self.target, self.anchor, lambda text, _, end: writing.cut_after(text, end)
        )
