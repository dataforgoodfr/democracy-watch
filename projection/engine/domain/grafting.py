"""Applique un patch à l'arbre d'un article : le texte projeté, avec l'origine de chaque mot.

Même composition que `patch.apply` (en parallèle sur les positions de l'article de base), mais sur
des nœuds : un alinéa ou un mot que le patch ne touche pas est repris tel quel, avec son
identifiant et son origine. Les splices restent des plages de caractères : les mots sont retrouvés
après coup, en découpant le nouveau texte de l'alinéa et en suivant d'où vient chaque caractère.
Les identifiants des mots et alinéas écrits ne dépendent que de leur origine (voir `identity`).
"""

import dataclasses
from collections import Counter

from engine.domain import identity
from engine.domain.patch import Patch, Splice, compose_lines, ordered
from engine.domain.tree import ArticleTree, Origin, Paragraph, Word, paragraph_of, tokenize


def _written(
    origin: str, text_uid: str, lines: tuple[str, ...], counter: Counter[str]
) -> tuple[Paragraph, ...]:
    """Alinéas entièrement écrits par `origin`, dans l'ordre ; `counter` : rangs déjà pris."""
    paragraphs = []
    for line in lines:
        counter[origin] += 1
        id = identity.written_paragraph_id(origin, counter[origin])
        paragraphs.append(paragraph_of(id, line, Origin(text_uid, origin or None)))
    return tuple(paragraphs)


def _taken(paragraph: Paragraph) -> Counter[str]:
    """Plus grand rang de mot déjà écrit dans l'alinéa, par origine."""
    taken: Counter[str] = Counter()
    for word in paragraph.words:
        origin, found, rank = word.id.rsplit("/", 1)[-1].rpartition(".m")
        if found:
            taken[origin] = max(taken[origin], int(rank))
    return taken


def _edited(paragraph: Paragraph, text_uid: str, splices: list[Splice]) -> Paragraph:
    """L'alinéa après des modifications de caractères sans conflit entre elles.

    Un mot que les modifications laissent intact est repris ; tout autre mot est un mot écrit, par
    l'origine de la modification qui le touche. Un mot coupé en son milieu est donc réécrit en
    entier : il est le résultat de la modification.
    """
    old = paragraph.text
    by_start: dict[int, Word] = {}
    position = 0
    for word in paragraph.words:
        by_start[position] = word
        position += len(word.text)
    pieces: list[str] = []
    labels: list[int] = []  # par caractère du nouveau texte : position d'origine, ou -1 si écrit
    ranges: list[tuple[int, int, str]] = []  # plage écrite du nouveau texte, et son origine
    cursor = size = 0
    for start, end, splice in ordered((s.span[0], s.span[1], s) for s in splices if s.span):
        new = str(splice.new)
        pieces += [old[cursor:start], new]
        labels += [*range(cursor, start), *[-1] * len(new)]
        size += start - cursor
        ranges.append((size, size + len(new), splice.origin))
        size += len(new)
        cursor = end
    pieces.append(old[cursor:])
    labels += range(cursor, len(old))

    taken = _taken(paragraph)
    words: list[Word] = []
    offset = 0
    for token in tokenize("".join(pieces)):
        span = labels[offset : offset + len(token)]
        kept = by_start.get(span[0])
        if kept and kept.text == token and span == [*range(span[0], span[0] + len(token))]:
            words.append(kept)
        else:
            origin = _origin_of(offset, offset + len(token), ranges)
            taken[origin] += 1
            id = identity.written_word_id(paragraph.id, origin, taken[origin])
            words.append(Word(id, token, Origin(text_uid, origin or None)))
        offset += len(token)
    return Paragraph(paragraph.id, tuple(words))


def _origin_of(start: int, end: int, ranges: list[tuple[int, int, str]]) -> str:
    """Origine d'un mot écrit : la modification qui le recouvre, sinon celle qui le touche.

    Une suppression pure laisse une plage vide : elle ne l'emporte que si rien d'autre ne recouvre
    le mot (deux mots fusionnés par la suppression de l'espace qui les séparait).
    """
    covering = [origin for lo, hi, origin in ranges if lo < end and start < hi]
    touching = [origin for lo, hi, origin in ranges if lo <= end and start <= hi]
    return (covering or touching or [origin for _, _, origin in ranges])[0]


def graft(article: ArticleTree, patch: Patch, text_uid: str) -> ArticleTree:
    """L'arbre de l'article après un patch sans conflit interne, calculé contre `article`.

    `text_uid` : le texte dont c'est l'étape, pour l'origine des mots écrits. Une suppression
    d'article rend un arbre sans alinéa.
    """
    counter: Counter[str] = Counter()
    for splice in patch:
        if splice.span is None:
            new = splice.new
            lines = (new,) if isinstance(new, str) else new
            written = _written(splice.origin, text_uid, lines, counter)
            return dataclasses.replace(article, paragraphs=written)
    paragraphs = list(article.paragraphs)
    for index in sorted({s.line for s in patch if s.line is not None}):
        same_line = [s for s in patch if s.line == index]
        paragraphs[index] = _edited(paragraphs[index], text_uid, same_line)
    line_splices = ordered(
        (s.span[0], s.span[1], s) for s in patch if s.line is None and s.span is not None
    )
    edits = []
    for start, end, splice in line_splices:
        assert not isinstance(splice.new, str)
        edits.append((start, end, _written(splice.origin, text_uid, splice.new, counter)))
    return dataclasses.replace(article, paragraphs=compose_lines(tuple(paragraphs), edits))
