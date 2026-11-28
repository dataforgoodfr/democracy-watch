"""Algorithmes de projection comparés aux textes officiels par l'évaluation.

- base.py : Algorithm, la classe dont hérite chaque algorithme ;
- un module par algorithme. Les algorithmes lancés par défaut sont ceux importés ici.
"""

from projection.eval.algorithms.base import Algorithm, all_algorithms
from projection.eval.algorithms.identity import Identity

__all__ = ["Algorithm", "Identity", "all_algorithms"]
