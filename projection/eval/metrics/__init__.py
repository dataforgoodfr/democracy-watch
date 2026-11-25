"""Métriques de l'évaluation de la projection (#73).

    rows = [row for step in steps for row in score_step(step, predict(step))]
    summary = summarize(rows)  # {"tous" | "modifies" | "inchanges": GroupSummary}

- base.py    : Metric, la classe dont hérite chaque métrique ;
- formats.py : ce que les métriques reçoivent et renvoient (#154) ;
- scoring.py : appariement des articles par numéro, résumé par groupe (GROUPS) ;
- text.py    : normalisation des textes ;
- un module par métrique. Les métriques utilisées par défaut sont celles importées ici.
"""

from projection.eval.metrics.base import Metric, all_metrics
from projection.eval.metrics.formats import GroupSummary, Row
from projection.eval.metrics.identical import Identical
from projection.eval.metrics.presence import Presence
from projection.eval.metrics.scoring import GROUPS, score_step, summarize
from projection.eval.metrics.words import Words

__all__ = [
    "GROUPS",
    "GroupSummary",
    "Identical",
    "Metric",
    "Presence",
    "Row",
    "Words",
    "all_metrics",
    "score_step",
    "summarize",
]
