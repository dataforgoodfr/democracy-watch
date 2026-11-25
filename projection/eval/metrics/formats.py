"""Formats d'entrée et de sortie des métriques (#154).

Entrée : une étape du corpus (format de corpus.py, dont les noms de champs restent ceux des
données) et les articles prédits pour sa sortie.
Sortie : une Row par article (les scores de chaque métrique), puis un SubsetSummary par
sous-ensemble d'articles. Les deux passent en JSON par dataclasses.asdict.
"""

from dataclasses import dataclass
from typing import NotRequired, TypedDict


class CorpusArticle(TypedDict):
    """Un article au format du corpus, officiel ou prédit."""

    numero: str  # « PREMIER », « 5 BIS »
    lignes: list[str]  # un alinéa par élément
    supprime: NotRequired[bool]


class CorpusText(TypedDict):
    ref: str
    articles: list[CorpusArticle]


class Step(TypedDict):
    """Une étape du corpus, réduite à ce que lisent les métriques et les prédicteurs."""

    id: str  # « <dossier>:<etape> »
    entree: CorpusText
    sortie: CorpusText
    amendements: list[dict]  # déposés sur l'entrée, champs de tricoteuses.Amendement sans l'auteur


class Stats(TypedDict):
    mean: float | None  # None : sous-ensemble vide
    median: float | None


@dataclass
class Row:
    """Résultat d'un article : les scores de chaque métrique, par nom de métrique."""

    id: str  # l'étape du corpus
    numero: str
    changed: bool  # la cible modifie l'article (texte, création ou suppression)
    scores: dict[str, dict[str, float]]


@dataclass
class SubsetSummary:
    """Résumé d'un sous-ensemble d'articles : leur nombre, et la moyenne et la médiane de chaque
    score."""

    articles: int
    scores: dict[str, dict[str, Stats]]
