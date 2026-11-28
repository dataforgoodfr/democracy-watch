from projection.eval.algorithms.base import Algorithm
from projection.eval.formats import CorpusArticle


class Identity(Algorithm):
    """Référence : recopie l'entrée sans appliquer aucun amendement. Le score obtenu sans rien
    faire, toujours lancé par la commande."""

    name = "identity"

    def predict(self, entree: list[CorpusArticle], amendements: list[dict]) -> list[CorpusArticle]:
        return entree
