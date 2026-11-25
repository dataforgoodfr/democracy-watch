from projection.eval.formats import CorpusArticle
from projection.eval.predictors.base import Predictor


class CopyInput(Predictor):
    """Référence : recopie l'entrée sans appliquer aucun amendement. Le score à battre, toujours
    affiché par la commande."""

    name = "copy_input"

    def predict(self, entree: list[CorpusArticle], amendements: list[dict]) -> list[CorpusArticle]:
        return entree
