"""Prédicteurs de l'évaluation : les algorithmes de projection comparés aux textes officiels.

- base.py : Predictor, la classe dont hérite chaque prédicteur ;
- un module par prédicteur. Les prédicteurs lancés par défaut sont ceux importés ici.
"""

from projection.eval.predictors.base import Predictor, all_predictors
from projection.eval.predictors.copy_input import CopyInput

__all__ = ["CopyInput", "Predictor", "all_predictors"]
