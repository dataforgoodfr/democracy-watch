"""Tricoteuses → types du moteur : seul endroit où le moteur rencontre les champs de la source.

Les objets sont lus par attributs ; le module `datasources.tricoteuses` n'est importé que pour les
types, jamais à l'exécution (le moteur ne dépend pas de la source).
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from engine.domain.documents import Amendment, Article, Text

if TYPE_CHECKING:
    from projection.datasources import tricoteuses


def article_from(article: tricoteuses.Article) -> Article:
    """Un `Article` du moteur."""
    return Article(article.numero, tuple(article.lignes), article.inchange, article.issu_de_plage)


def text_from(uid: str, articles: Iterable[tricoteuses.Article]) -> Text:
    """Un `Text` du moteur : l'`uid` du texte et ses articles, dans l'ordre."""
    return Text(uid, tuple(article_from(article) for article in articles))


def amendment_from(amendement: tricoteuses.Amendement) -> Amendment:
    """Un `Amendment` du moteur. Le champ `alinea` n'est qu'un indice : il n'est pas repris."""
    return Amendment(
        number=amendement.numero,
        target_label=amendement.article_vise,
        body_html=amendement.dispositif,
        id=amendement.uid,
        parent_id=amendement.parent_uid,
        twin_group=amendement.id_identique,
        decided_at=amendement.date_sort,
    )
