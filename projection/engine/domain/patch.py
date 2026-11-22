"""Patch : le changement d'un texte, calculé contre une base précise.

Un patch est un ensemble de `Splice`, chacun remplaçant une plage dans une séquence. Ils se
calculent tous contre les positions du MÊME texte de base et s'appliquent en parallèle : deux
patchs issus de la même base se fusionnent s'ils ne se `conflicts` pas. Un patch n'a de sens que
contre sa base ; pour changer de base, on réévalue l'opération qui l'a produit, jamais on ne
décale des positions.

Trois niveaux de séquence, une seule règle de conflit :

- l'article lui-même (`span` None) : le remplacer, ou le supprimer (`new` vide) ;
- les alinéas d'un article (`line` None) : `span` est une plage d'alinéas, `new` des alinéas ;
- les caractères d'un alinéa (`line` donné) : `span` est une plage de caractères, `new` un `str`.
"""

import dataclasses
from collections.abc import Iterable
from typing import cast


@dataclasses.dataclass(frozen=True)
class Splice:
    """Remplace `span` (début inclus, fin exclue) d'une séquence de l'article par `new`.

    `span` vide (début = fin) : insertion.
    """

    article: str
    span: tuple[int, int] | None
    new: str | tuple[str, ...]
    line: int | None = None

    @classmethod
    def on_article(cls, article: str, new: tuple[str, ...]) -> Splice:
        """Remplace l'article entier par `new` ; `new` vide : suppression de l'article."""
        return cls(article, None, new)

    @classmethod
    def on_lines(cls, article: str, start: int, end: int, new: tuple[str, ...]) -> Splice:
        """Remplace les alinéas `start:end` de l'article par `new`."""
        return cls(article, (start, end), new)

    @classmethod
    def on_chars(cls, article: str, line: int, start: int, end: int, new: str) -> Splice:
        """Remplace les caractères `start:end` de l'alinéa `line` par `new`."""
        return cls(article, (start, end), new, line)


Patch = tuple[Splice, ...]


def _lines_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Deux plages d'alinéas : même point d'insertion, insertion à l'intérieur, ou recouvrement.

    Des bords qui se touchent ne sont pas un conflit.
    """
    a_inserts, b_inserts = a[0] == a[1], b[0] == b[1]
    if a_inserts and b_inserts:
        return a[0] == b[0]
    if a_inserts:
        return b[0] < a[0] < b[1]
    if b_inserts:
        return a[0] < b[0] < a[1]
    return a[0] < b[1] and b[0] < a[1]


def conflicts(a: Splice, b: Splice) -> bool:
    """Vrai si deux splices ne peuvent pas s'appliquer ensemble.

    Le remplacement de l'article entier est en conflit avec tout le reste du même article. Deux
    plages d'alinéas : voir `_lines_overlap`. Deux plages de caractères du même alinéa : elles ne
    doivent pas se toucher, car les règles d'écriture ajustent les espaces aux bords d'une
    modification. Une plage de caractères est en conflit avec le remplacement ou la suppression de
    son alinéa, pas avec une insertion d'alinéas à côté.
    """
    if a.article != b.article:
        return False
    if a.span is None or b.span is None:
        return True
    if a.line is not None and b.line is not None:
        return a.line == b.line and a.span[0] <= b.span[1] and b.span[0] <= a.span[1]
    if a.line is not None:
        return b.span[0] <= a.line < b.span[1]
    if b.line is not None:
        return a.span[0] <= b.line < a.span[1]
    return _lines_overlap(a.span, b.span)


def _ordered[T](edits: Iterable[tuple[int, int, T]]) -> list[tuple[int, int, T]]:
    """Remplacements `(début, fin, nouveau)` dans l'ordre de la séquence.

    À position égale, une insertion passe avant un remplacement.
    """
    return sorted(edits, key=lambda edit: (edit[0], edit[0] != edit[1]))


def _compose_text(text: str, edits: Iterable[tuple[int, int, str]]) -> str:
    """Applique des remplacements sans conflit, en parallèle sur les positions de `text`."""
    pieces: list[str] = []
    position = 0
    for start, end, new in _ordered(edits):
        pieces += [text[position:start], new]
        position = end
    return "".join(pieces) + text[position:]


def _compose_lines(
    lines: tuple[str, ...], edits: Iterable[tuple[int, int, tuple[str, ...]]]
) -> tuple[str, ...]:
    """Applique des remplacements sans conflit, en parallèle sur les positions de `lines`."""
    result: tuple[str, ...] = ()
    position = 0
    for start, end, new in _ordered(edits):
        result += lines[position:start] + new
        position = end
    return result + lines[position:]


def deletes_article(patch: Patch) -> bool:
    """Vrai si le patch supprime l'article."""
    return any(splice.span is None and not splice.new for splice in patch)


def apply(lines: tuple[str, ...], patch: Patch) -> tuple[str, ...]:
    """Alinéas de l'article après application d'un patch sans conflit interne.

    Une suppression d'article rend aucun alinéa.
    """
    for splice in patch:
        if splice.span is None:
            return cast(tuple[str, ...], splice.new)
    texts = list(lines)
    for index in {splice.line for splice in patch if splice.line is not None}:
        texts[index] = _compose_text(
            texts[index],
            (
                (splice.span[0], splice.span[1], cast(str, splice.new))
                for splice in patch
                if splice.line == index and splice.span is not None
            ),
        )
    return _compose_lines(
        tuple(texts),
        (
            (splice.span[0], splice.span[1], cast(tuple[str, ...], splice.new))
            for splice in patch
            if splice.line is None and splice.span is not None
        ),
    )
