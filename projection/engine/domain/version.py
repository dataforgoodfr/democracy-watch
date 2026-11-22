"""Version : un état complet du texte, immuable.

Appliquer un amendement ne modifie jamais une version : cela en crée une nouvelle, qui partage avec
la précédente tous les articles (et donc tous les alinéas et mots) inchangés. La version d'origine,
`Version.of(text)`, sert de référence : c'est le texte sur lequel les amendements sont rédigés, donc
celui où se lisent leurs numéros d'alinéa.
"""

import dataclasses

from engine.domain.documents import Text
from engine.domain.normalization import normalize
from engine.domain.refusal import Reason, Refusal
from engine.domain.tree import ArticleTree, Word, article_of


@dataclasses.dataclass(frozen=True)
class Version:
    """Les articles du texte `text_uid` à un moment du rejeu.

    `parent` : la version dont celle-ci est issue, `None` pour la version d'origine ; `applied` :
    les amendements appliqués depuis l'origine, dans l'ordre.
    """

    text_uid: str
    articles: tuple[ArticleTree, ...]
    parent: Version | None = None
    applied: tuple[str, ...] = ()

    @classmethod
    def of(cls, text: Text) -> Version:
        """La version d'origine : le texte d'entrée de l'étape, normalisé comme à la lecture."""
        articles = tuple(
            article_of(
                text.uid,
                dataclasses.replace(a, lines=tuple(normalize(line) for line in a.lines)),
            )
            for a in text.articles
        )
        return cls(text.uid, articles)

    def find(self, number: str) -> ArticleTree:
        """L'unique article `number` ; sinon `Refusal`."""
        found = [article for article in self.articles if article.number == number]
        if len(found) != 1:
            raise Refusal(Reason.UNRESOLVED_ARTICLE, f"{len(found)} article(s) « {number} »")
        return found[0]

    def replace(self, article: ArticleTree, *amendments: str) -> Version:
        """La version où `article` remplace l'article de même identifiant ; le reste est partagé.

        `amendments` : les amendements qui ont produit ce nouvel article.
        """
        articles = tuple(article if a.id == article.id else a for a in self.articles)
        return Version(self.text_uid, articles, self, (*self.applied, *amendments))

    def word(self, word_id: str) -> Word:
        """Le mot d'identifiant `word_id` ; `KeyError` s'il n'est pas dans cette version."""
        for article in self.articles:
            for paragraph in article.paragraphs:
                for word in paragraph.words:
                    if word.id == word_id:
                        return word
        raise KeyError(word_id)
