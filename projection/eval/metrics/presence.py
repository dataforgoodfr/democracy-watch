from projection.eval.metrics.base import Metric
from projection.eval.metrics.text import normalize


class Presence(Metric):
    """L'article existe-t-il dans la prédiction exactement quand il existe dans la cible : gardé,
    créé ou supprimé à bon escient (lecture de « articles exacts » dans #73) ?"""

    name = "presence"

    def score(self, prediction: str, cible: str) -> dict[str, float]:
        return {"presence": float(bool(normalize(prediction)) == bool(normalize(cible)))}
