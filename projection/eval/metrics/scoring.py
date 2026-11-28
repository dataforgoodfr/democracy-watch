"""Score d'une prédiction : article par article, puis résumé par sous-ensemble d'articles."""

from collections.abc import Callable, Sequence
from statistics import fmean, median

from projection.eval.formats import CorpusArticle, Row, Stats, Step, SubsetSummary
from projection.eval.metrics.base import Metric, all_metrics
from projection.eval.metrics.text import normalize

# Sous-ensembles d'articles sur lesquels le résumé est calculé : un nom et un filtre. Ceux que
# la cible ne modifie pas sont à part : une prédiction qui recopie l'entrée y est parfaite sans
# rien projeter.
ARTICLE_SUBSETS: dict[str, Callable[[Row], bool]] = {
    "changed": lambda row: row.changed,
    "all": lambda row: True,
    "unchanged": lambda row: not row.changed,
}


def texts_by_number(articles: list[CorpusArticle]) -> dict[str, str]:
    """{numéro : texte de l'article, alinéas joints, ou "" s'il est supprimé}."""
    return {a["numero"]: "" if a.get("supprime") else "\n".join(a["lignes"]) for a in articles}


def score_step(
    step: Step, prediction: list[CorpusArticle], metrics: Sequence[Metric] | None = None
) -> list[Row]:
    """Une Row par article de l'étape, apparié par numéro entre entrée, cible et prédiction.

    Un article absent de la prédiction compte comme supprimé. Par défaut, toutes les métriques.
    """
    metrics = all_metrics() if metrics is None else metrics
    inputs = texts_by_number(step["entree"]["articles"])
    targets = texts_by_number(step["sortie"]["articles"])
    predicted = texts_by_number(prediction)
    rows = []
    for number in dict.fromkeys([*inputs, *targets, *predicted]):
        before, target = inputs.get(number, ""), targets.get(number, "")
        scores = {m.name: m.score(predicted.get(number, ""), target) for m in metrics}
        rows.append(Row(step["id"], number, normalize(before) != normalize(target), scores))
    return rows


def stats(values: list[float]) -> Stats:
    return {
        "mean": fmean(values) if values else None,
        "median": median(values) if values else None,
    }


def summarize(rows: list[Row]) -> dict[str, SubsetSummary]:
    """Un SubsetSummary par sous-ensemble de ARTICLE_SUBSETS : moyenne et médiane des scores."""
    summary = {}
    for subset, keep in ARTICLE_SUBSETS.items():
        kept = [row for row in rows if keep(row)]
        values: dict[str, dict[str, list[float]]] = {}
        for row in kept:
            for metric, scores in row.scores.items():
                for key, value in scores.items():
                    values.setdefault(metric, {}).setdefault(key, []).append(value)
        scores = {m: {k: stats(v) for k, v in keys.items()} for m, keys in values.items()}
        summary[subset] = SubsetSummary(len(kept), scores)
    return summary
