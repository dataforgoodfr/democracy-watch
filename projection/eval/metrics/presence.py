from projection.eval.metrics.base import Metric


class Presence(Metric):
    """L'article existe-t-il dans la prédiction exactement quand il existe dans la cible : gardé,
    créé ou supprimé à bon escient (lecture de « articles exacts » dans #73) ?"""

    name = "presence"

    def score(self, prediction: str, target: str) -> dict[str, float]:
        # Un article absent ou supprimé arrive vide (voir scoring.texts_by_number).
        exists_predicted, exists_official = bool(prediction.strip()), bool(target.strip())
        return {"presence": float(exists_predicted == exists_official)}
