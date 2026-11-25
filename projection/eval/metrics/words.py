from difflib import SequenceMatcher

from projection.eval.metrics.base import Metric
from projection.eval.metrics.text import tokens


class Words(Metric):
    """Mots ajoutés et retirés par la prédiction par rapport à la cible, et la précision, le
    rappel et le F1 qui en découlent (« mots enlevés et ajoutés » dans #73).

    Les deux textes sont alignés par diff : une phrase déplacée ne décale pas tout le reste.
    """

    name = "mots"

    def score(self, prediction: str, cible: str) -> dict[str, float]:
        predicted, expected = tokens(prediction), tokens(cible)
        matcher = SequenceMatcher(None, predicted, expected, autojunk=False)
        common = sum(block.size for block in matcher.get_matching_blocks())
        # Deux textes vides (article supprimé des deux côtés) : prédiction parfaite.
        precision = common / len(predicted) if predicted else float(not expected)
        recall = common / len(expected) if expected else float(not predicted)
        return {
            "ajoutes": len(predicted) - common,
            "retires": len(expected) - common,
            "precision": precision,
            "rappel": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        }
