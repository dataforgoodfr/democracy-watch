"""Score d'une prédiction : chaque article passé à chaque métrique, puis résumé par groupe."""

from collections.abc import Callable, Sequence
from statistics import fmean, median

from projection.eval.metrics.base import Metric, all_metrics
from projection.eval.metrics.formats import CorpusArticle, GroupSummary, Row, Stats, Step
from projection.eval.metrics.text import normalize

# Groupes d'articles du résumé. Ceux que la cible ne modifie pas sont à part : une prédiction
# qui recopie l'entrée y est parfaite sans rien projeter.
GROUPS: dict[str, Callable[[Row], bool]] = {
    "tous": lambda row: True,
    "modifies": lambda row: row.modifie,
    "inchanges": lambda row: not row.modifie,
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
    entree = texts_by_number(step["entree"]["articles"])
    cible = texts_by_number(step["sortie"]["articles"])
    predicted = texts_by_number(prediction)
    rows = []
    for number in dict.fromkeys([*entree, *cible, *predicted]):
        e, c, p = entree.get(number, ""), cible.get(number, ""), predicted.get(number, "")
        scores = {metric.name: metric.score(p, c) for metric in metrics}
        rows.append(Row(step["id"], number, normalize(e) != normalize(c), scores))
    return rows


def stats(values: list[float]) -> Stats:
    return {
        "moyenne": fmean(values) if values else None,
        "mediane": median(values) if values else None,
    }


def summarize(rows: list[Row]) -> dict[str, GroupSummary]:
    """Un GroupSummary par groupe de GROUPS : moyenne et médiane de chaque score."""
    summary = {}
    for group, keep in GROUPS.items():
        kept = [row for row in rows if keep(row)]
        values: dict[str, dict[str, list[float]]] = {}
        for row in kept:
            for metric, scores in row.scores.items():
                for key, value in scores.items():
                    values.setdefault(metric, {}).setdefault(key, []).append(value)
        scores = {m: {k: stats(v) for k, v in keys.items()} for m, keys in values.items()}
        summary[group] = GroupSummary(len(kept), scores)
    return summary
