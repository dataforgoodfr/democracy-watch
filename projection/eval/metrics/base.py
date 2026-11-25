"""La classe dont hérite chaque métrique."""

import inspect
from abc import ABC, abstractmethod
from typing import ClassVar

PACKAGE = __name__.rpartition(".")[0]


class Metric(ABC):
    """Une métrique : (prédiction, cible) → score(s), comme dans la RFC.

    Pour en ajouter une : un module de ce paquet, avec une sous-classe qui définit `name` et
    `score`, importé dans __init__.py. Elle est alors utilisée par défaut (voir all_metrics).
    """

    name: ClassVar[str]  # clé de ses scores dans Row.scores et GroupSummary.scores

    @abstractmethod
    def score(self, prediction: str, cible: str) -> dict[str, float]:
        """Les scores d'un article, textes prédit et officiel ("" s'il est absent ou supprimé)."""


def all_metrics() -> list[Metric]:
    """Une instance de chaque métrique de ce paquet, dans l'ordre où elles sont importées.

    Une sous-classe définie ailleurs (dans un test, par exemple) n'est pas prise par défaut.
    """
    found: list[Metric] = []
    todo: list[type[Metric]] = [Metric]
    while todo:
        cls = todo.pop(0)
        todo += cls.__subclasses__()
        if not inspect.isabstract(cls) and cls.__module__.startswith(f"{PACKAGE}."):
            found.append(cls())
    return found
