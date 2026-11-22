"""Cibles d'une opération et résolution : de la désignation à des indices.

Les positions d'alinéa sont celles du texte d'entrée de l'étape (1 = premier ; -1 = dernier,
-2 = avant-dernier).
"""

import dataclasses

from engine.domain.refusal import Reason, Refusal


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
