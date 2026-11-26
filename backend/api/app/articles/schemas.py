"""Articles : emplacements d'un texte (titre, articles réels, intervalles entre articles)."""

from pydantic import BaseModel

from ..dossiers.schemas import DossierRef
from ..textes.schemas import TexteRef


class ArticleRef(BaseModel):
    uid: str  # « <uid du texte>-<position> », stable d'un chargement à l'autre
    number: str | None  # NULL pour un emplacement
    label: str


class Article(ArticleRef):
    texte: TexteRef
    dossier: DossierRef
    position: int  # 0 = titre, 10k = article de rang k, 10k + 5 = après l'article k
    is_placeholder: bool  # titre ou intervalle entre articles, pas un article réel
    is_deleted: bool
    content: str | None
