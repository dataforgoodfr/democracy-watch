from projection.eval.metrics.base import Metric
from projection.eval.metrics.text import normalize


class Identical(Metric):
    """L'article prédit est-il identique à la cible, après normalisation (« articles identiques »
    dans #73) ? Sévère : un seul mot faux et l'article compte comme raté."""

    name = "identical"

    def score(self, prediction: str, target: str) -> dict[str, float]:
        return {"identical": float(normalize(prediction) == normalize(target))}
