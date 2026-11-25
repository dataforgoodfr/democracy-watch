"""La classe dont hérite chaque algorithme."""

from abc import ABC, abstractmethod
from typing import ClassVar

from projection.eval.discovery import instances
from projection.eval.formats import CorpusArticle


class Algorithm(ABC):
    """Un algorithme de projection : la fonction F de la RFC, entrée → sortie. Il ne voit jamais
    la sortie officielle.

    Pour en ajouter un : un module de ce paquet, avec une sous-classe qui définit `name` et
    `predict`, importé dans __init__.py. Il est alors lancé par défaut (voir all_algorithms).
    """

    name: ClassVar[str]  # nom donné à la commande et affiché dans les résultats

    @abstractmethod
    def predict(self, entree: list[CorpusArticle], amendements: list[dict]) -> list[CorpusArticle]:
        """Les articles prédits pour la sortie, à partir des articles du texte d'entrée et des
        amendements déposés dessus."""


def all_algorithms() -> list[Algorithm]:
    """Une instance de chaque algorithme de ce paquet."""
    return instances(Algorithm, __name__.rpartition(".")[0])
