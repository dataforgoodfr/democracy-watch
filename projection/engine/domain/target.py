"""Cibles d'une opération et résolution : de la désignation à des indices.

Les positions d'alinéa sont celles du texte d'entrée de l'étape (1 = premier ; -1 = dernier,
-2 = avant-dernier).
"""

import dataclasses

from engine.domain.refusal import Reason, Refusal
from engine.domain.tree import ArticleTree


@dataclasses.dataclass(frozen=True)
class Alineas:
    """Un ou plusieurs alinéas désignés par leur position (listes, plages développées)."""

    positions: tuple[int, ...]


@dataclasses.dataclass(frozen=True)
class WholeArticle:
    """L'article entier : « cet article » (`number` None) ou « l'article 3 » (`number` = « 3 »)."""

    number: str | None = None


@dataclasses.dataclass(frozen=True)
class Anaphor:
    """« cet alinéa », « le même alinéa » : l'antécédent n'est pas encore résolu."""


Target = Alineas | WholeArticle | Anaphor


def resolve(target: Target, article_number: str, count: int) -> tuple[int, ...]:
    """Indices 0-based, triés et sans doublon, des alinéas visés dans un texte de `count` alinéas.

    Une position négative compte depuis la fin (-1 = dernier). Une position nulle ou hors du texte
    est un refus : on ne propose jamais l'alinéa le plus proche.
    """
    match target:
        case Alineas(positions):
            indices = set()
            for position in positions:
                index = position - 1 if position > 0 else count + position
                if position == 0 or not 0 <= index < count:
                    raise Refusal(
                        Reason.TARGET_NOT_FOUND,
                        f"alinéa {position} absent d'un texte de {count} alinéas",
                    )
                indices.add(index)
            return tuple(sorted(indices))
        case WholeArticle(number):
            if number not in (None, article_number):
                raise Refusal(
                    Reason.UNRESOLVED_ARTICLE,
                    f"article {number} visé, article {article_number} projeté",
                )
            return tuple(range(count))
        case Anaphor():
            raise Refusal(Reason.OUT_OF_SCOPE, "antécédent d'une anaphore non résolu")


def remap(target: Target, reference: ArticleTree, current: ArticleTree) -> Target:
    """La même cible, lue dans la version de référence puis retrouvée dans la version courante.

    Le numéro d'alinéa d'un amendement est celui du texte sur lequel il a été rédigé : on en tire un
    identifiant stable, puis la position de cet alinéa dans `current`. Un alinéa inséré plus tôt ne
    décale donc rien ; un alinéa réécrit ou supprimé plus tôt est `TARGET_GONE`. Les autres cibles
    ne dépendent pas des positions.
    """
    if not isinstance(target, Alineas):
        return target
    positions = []
    for index in resolve(target, reference.number, len(reference.paragraphs)):
        paragraph = reference.paragraphs[index]
        try:
            positions.append(current.find(paragraph.id) + 1)
        except ValueError:
            raise Refusal(
                Reason.TARGET_GONE, f"alinéa {index + 1} ({paragraph.id}) absent de la version"
            ) from None
    return Alineas(tuple(positions))


def remap_insertion(
    target: Target, reference: ArticleTree, current: ArticleTree, after: bool
) -> tuple[Target, bool]:
    """Comme `remap`, pour une insertion : la cible et le sens (après/avant) dans `current`.

    Une insertion ne dépend pas du texte de l'alinéa visé, seulement de l'endroit où il était.
    Si cet alinéa a disparu (supprimé ou réécrit plus tôt), on insère avant le premier alinéa
    suivant qui subsiste (« après ») ou après le dernier alinéa précédent qui subsiste (« avant ») ;
    à défaut, en fin ou en début d'article.
    """
    try:
        return remap(target, reference, current), after
    except Refusal as refusal:
        if refusal.reason is not Reason.TARGET_GONE or not isinstance(target, Alineas):
            raise
        indices = resolve(target, reference.number, len(reference.paragraphs))
        if len(indices) != 1:
            raise
    index = indices[0]
    alive = {paragraph.id for paragraph in current.paragraphs}
    around = reference.paragraphs[index + 1 :] if after else reversed(reference.paragraphs[:index])
    for paragraph in around:
        if paragraph.id in alive:
            return Alineas((current.find(paragraph.id) + 1,)), not after
    return WholeArticle(), after
