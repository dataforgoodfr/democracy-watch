"""Effet d'une opération : ce qu'elle écrit et ce qu'elle lit, en identifiants stables.

On compare des effets, jamais des rédactions : deux opérations interfèrent si l'une écrit ce que
l'autre écrit ou lit. Réécrire un nœud écrit tous ses descendants, donc l'intersection détecte
qu'un alinéa réécrit contient le mot qu'une autre opération modifie.
"""

import dataclasses

from engine.domain.patch import Patch
from engine.domain.tree import ArticleTree


@dataclasses.dataclass(frozen=True)
class Effect:
    """Ce qu'une opération a écrit et lu.

    `writes` : identifiants des mots, alinéas et articles modifiés ou retirés, plus une position
    symbolique pour ce qui s'ajoute (`after:ID` : juste après le nœud `ID` ; `start:ID` : au début
    du nœud `ID`). `reads` : les alinéas dont l'opération a eu besoin pour se situer.
    """

    writes: frozenset[str] = frozenset()
    reads: frozenset[str] = frozenset()

    def interferes(self, other: Effect) -> bool:
        """Vrai si l'un écrit ce que l'autre écrit ou lit."""
        return bool(
            self.writes & (other.writes | other.reads) or other.writes & (self.writes | self.reads)
        )


def _subtree(article: ArticleTree, start: int, end: int) -> set[str]:
    """Identifiants des alinéas `start:end` et de tous leurs mots."""
    ids: set[str] = set()
    for paragraph in article.paragraphs[start:end]:
        ids.add(paragraph.id)
        ids.update(word.id for word in paragraph.words)
    return ids


def effect_of(article: ArticleTree, patch: Patch) -> Effect:
    """L'effet d'un patch calculé contre `article`."""
    writes: set[str] = set()
    reads: set[str] = set()
    for splice in patch:
        if splice.span is None:
            writes |= {article.id} | _subtree(article, 0, len(article.paragraphs))
            continue
        start, end = splice.span
        if splice.line is None:
            if start == end:
                before = article.paragraphs[start - 1].id if start else None
                writes.add(f"after:{before}" if before else f"start:{article.id}")
            else:
                writes |= _subtree(article, start, end)
            continue
        paragraph = article.paragraphs[splice.line]
        reads.add(paragraph.id)
        position = 0
        previous = None
        for word in paragraph.words:
            lo, hi = position, position + len(word.text)
            position = hi
            if start == end:
                if hi <= start:
                    previous = word.id
                if lo < start < hi:
                    writes.add(word.id)  # insertion dans un mot : il est réécrit en entier
            elif lo < end and start < hi:
                writes.add(word.id)
        if start == end:
            writes.add(f"after:{previous}" if previous else f"start:{paragraph.id}")
    return Effect(frozenset(writes), frozenset(reads))
