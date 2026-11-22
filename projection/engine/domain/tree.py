"""Arbre du texte : article → alinéa → mot, en lecture seule, chaque nœud avec son identifiant.

L'arbre double `documents.Article` (dont les alinéas sont des `str`) : le moteur planifie sur les
`str`, l'arbre dit d'où vient chaque mot. Un mot, une espace et un signe de ponctuation sont des
mots : le texte n'est pas analysé grammaticalement, il sert de matière à modifier. Joindre les mots
d'un alinéa redonne exactement son texte.

Les nœuds sont immuables : modifier un alinéa en crée un nouveau, qui partage les mots inchangés.
"""

import dataclasses
import functools
import re

from engine.domain import identity
from engine.domain.documents import Article

_WORDS = re.compile(r"\w+|\s|[^\w\s]")  # un mot, une espace ou un signe


@dataclasses.dataclass(frozen=True)
class Origin:
    """Ce qui a mis un mot dans un texte.

    `text` : uid du texte d'entrée de l'étape où le mot apparaît ; `amendment` : l'amendement qui
    l'a écrit, `None` s'il était déjà dans le texte d'entrée. `approximate` : le rattachement vient
    d'un alignement qui n'est pas certain (voir l'historique entre étapes).
    """

    text: str
    amendment: str | None = None
    approximate: bool = False


@dataclasses.dataclass(frozen=True)
class Word:
    """Un mot, avec son identifiant stable et son origine.

    `history` : les origines successives du mot dans les étapes précédentes, la plus ancienne
    d'abord ; vide pour un mot né dans ce texte.
    """

    id: str
    text: str
    origin: Origin
    history: tuple[Origin, ...] = ()

    @property
    def trail(self) -> tuple[Origin, ...]:
        """Tout le parcours du mot : de sa première apparition à son origine dans ce texte."""
        return (*self.history, self.origin)


@dataclasses.dataclass(frozen=True)
class Paragraph:
    """Un alinéa : ses mots, dans l'ordre."""

    id: str
    words: tuple[Word, ...]

    @functools.cached_property
    def text(self) -> str:
        """Le texte de l'alinéa."""
        return "".join(word.text for word in self.words)


@dataclasses.dataclass(frozen=True)
class ArticleTree:
    """Un article : ses alinéas, dans l'ordre. Le numéro d'alinéa est la position, jamais stocké."""

    id: str
    number: str
    paragraphs: tuple[Paragraph, ...]

    @property
    def lines(self) -> tuple[str, ...]:
        """Les textes des alinéas."""
        return tuple(paragraph.text for paragraph in self.paragraphs)

    def find(self, paragraph_id: str) -> int:
        """Position (0 = premier) de l'alinéa `paragraph_id` ; `ValueError` s'il n'y est plus."""
        for index, paragraph in enumerate(self.paragraphs):
            if paragraph.id == paragraph_id:
                return index
        raise ValueError(paragraph_id)


def tokenize(text: str) -> list[str]:
    """Découpe un texte en mots, espaces et signes. Sans perte : `"".join` redonne `text`."""
    return _WORDS.findall(text)


def paragraph_of(id: str, text: str, origin: Origin) -> Paragraph:
    """Un alinéa du texte d'entrée : ses mots portent des identifiants `id/m1`, `id/m2`…"""
    words = tuple(
        Word(identity.word_id(id, rank), token, origin)
        for rank, token in enumerate(tokenize(text), start=1)
    )
    return Paragraph(id, words)


@functools.lru_cache(maxsize=512)
def article_of(text_uid: str, article: Article) -> ArticleTree:
    """L'arbre d'un article du texte `text_uid` : tout vient du texte d'entrée.

    Mémoïsé : l'arbre est immuable et un même article sert à tous les amendements qui le visent.
    """
    article_id = identity.article_id(text_uid, article.number)
    origin = Origin(text_uid)
    paragraphs = tuple(
        paragraph_of(identity.paragraph_id(article_id, rank), line, origin)
        for rank, line in enumerate(article.lines, start=1)
    )
    return ArticleTree(article_id, article.number, paragraphs)
