"""La classe dont hérite chaque métrique."""

from abc import ABC, abstractmethod
from typing import ClassVar

from projection.eval.discovery import instances


class Metric(ABC):
    """Une métrique : (prédiction, cible) → score(s), comme dans la RFC.

    Pour en ajouter une : un module de ce paquet, avec une sous-classe qui définit `name` et
    `score`, importé dans __init__.py. Elle est alors utilisée par défaut (voir all_metrics).
    """

    name: ClassVar[str]  # clé de ses scores dans Row.scores et SubsetSummary.scores

    @abstractmethod
    def score(self, prediction: str, target: str) -> dict[str, float]:
        """Les scores d'un article, textes prédit et officiel ("" s'il est absent ou supprimé)."""


def all_metrics() -> list[Metric]:
    """Une instance de chaque métrique de ce paquet."""
    return instances(Metric, __name__.rpartition(".")[0])
