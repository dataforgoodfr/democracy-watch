"""Métriques de l'évaluation de la projection (#73).

    rows = [row for step in steps for row in score_step(step, prediction)]
    summary = summarize(rows)  # {"changed" | "all" | "unchanged": SubsetSummary}

- base.py    : Metric, la classe dont hérite chaque métrique ;
- scoring.py : appariement par numéro, résumé par sous-ensemble (ARTICLE_SUBSETS) ;
- text.py    : normalisation des textes ;
- un module par métrique. Les métriques utilisées par défaut sont celles importées ici.
"""

from projection.eval.formats import Row, SubsetSummary
from projection.eval.metrics.base import Metric, all_metrics
from projection.eval.metrics.identical import Identical
from projection.eval.metrics.presence import Presence
from projection.eval.metrics.scoring import ARTICLE_SUBSETS, score_step, summarize
from projection.eval.metrics.words import Words

__all__ = [
    "ARTICLE_SUBSETS",
    "Identical",
    "Metric",
    "Presence",
    "Row",
    "SubsetSummary",
    "Words",
    "all_metrics",
    "score_step",
    "summarize",
]
