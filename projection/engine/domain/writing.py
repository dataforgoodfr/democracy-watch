"""Règles d'écriture sur une ligne : repérage d'une ancre, insertion, recollement.

Fonctions pures sur des `str`. Les positions sont des indices de caractères du texte d'entrée.
"""

import dataclasses
import re

from engine.domain.refusal import Reason, Refusal


@dataclasses.dataclass(frozen=True)
class Anchor:
    """Mots cités qui repèrent un point du texte.

    `occurrence` : rang explicite (1, 2… ; -1 = dernière) ; None = l'ancre doit être unique.
    """

    text: str
    occurrence: int | None = None


_ATTACHED = ",.);"  # ponctuation collée au mot qui précède
_OPENING = "'(«-"  # ponctuation à laquelle le mot suivant se colle


def find_anchor(texts: list[str], anchor: Anchor) -> tuple[int, int, int]:
    """Repère l'ancre : (indice du texte, début, fin).

    Recherche par mots entiers et sensible à la casse : une frontière de mot n'est posée qu'aux
    bords de l'ancre qui sont des caractères de mot. Le trait d'union fait partie du mot
    (« porte » n'est pas dans « porte-parole ») ; l'apostrophe est une frontière. Un bord
    numérique ne coupe pas un nombre décimal (« 5 » n'est pas dans « 0,5 »). Les occurrences,
    non chevauchantes, sont comptées dans l'ordre sur l'ensemble des textes.
    """
    first, last = anchor.text[0], anchor.text[-1]
    before = (r"(?<![\w-])" if re.match(r"\w", first) else "") + (
        r"(?<!\d[,.])" if first.isdigit() else ""
    )
    after = (r"(?![\w-])" if re.match(r"\w", last) else "") + (
        r"(?![,.]\d)" if last.isdigit() else ""
    )
    pattern = re.compile(before + re.escape(anchor.text) + after)
    found = [
        (index, match.start(), match.end())
        for index, text in enumerate(texts)
        for match in pattern.finditer(text)
    ]
    rank = anchor.occurrence
    if rank is None and len(found) > 1:
        raise Refusal(Reason.QUOTE_MULTIPLE, f"« {anchor.text} » apparaît {len(found)} fois")
    if rank is None:
        rank = 1
    if rank == 0 or abs(rank) > len(found):
        raise Refusal(
            Reason.QUOTE_MISSING,
            f"« {anchor.text} » : occurrence {rank} absente ({len(found)} trouvée(s))",
        )
    return found[rank - 1 if rank > 0 else rank]


def insert_at(text: str, point: int, new: str) -> str:
    """Insère `new` au point donné, avec les espaces nécessaires.

    `new` est collé à gauche s'il commence par `,` `.` `)` `;`, ou si le texte de gauche finit par
    `'` `(` `«` `-` ; à droite, aucune espace n'est ajoutée devant une telle ponctuation, une
    espace existante ou la fin du texte, ni si `new` finit par `'` `(` `«` `-`.
    """
    left, right = text[:point], text[point:]
    if left and not left.endswith(" ") and left[-1] not in _OPENING and new[0] not in _ATTACHED:
        left += " "
    if (
        right
        and not right.startswith(" ")
        and right[0] not in _ATTACHED
        and new[-1] not in _OPENING
    ):
        right = " " + right
    return left + new + right


def insert_edge(text: str, new: str, start: bool) -> str:
    """Insère `new` au début de l'alinéa, ou à sa fin avant la ponctuation finale.

    La ponctuation finale (`.` `;` `:`, avec l'espace qui la précède) est conservée telle quelle ;
    si `new` en porte déjà une alors que l'alinéa en a une, c'est un refus.
    """
    if start:
        return insert_at(text, 0, new)
    tail = re.search(r"\s*[.;:]\Z", text)
    if tail is None:
        return insert_at(text, len(text), new)
    if new[-1] in ".;:":
        raise Refusal(Reason.OUT_OF_SCOPE, "double ponctuation finale")
    return insert_at(text[: tail.start()], tail.start(), new) + tail.group()


def cut(text: str, start: int, end: int) -> str:
    """Retire `text[start:end]` et recolle localement.

    Deux espaces qui se touchent n'en font qu'une ; l'espace avant `,` ou `.` disparaît ;
    l'espace en bord de ligne, à l'endroit de la coupe, aussi.
    """
    left, right = text[:start], text[end:]
    if right[:1] in (",", "."):
        left = left.removesuffix(" ")
    elif left.endswith(" ") and right.startswith(" "):
        right = right[1:]
    if not left:
        right = right.lstrip(" ")
    if not right:
        left = left.rstrip(" ")
    return left + right


def cut_after(text: str, end: int) -> str:
    """Retire tout ce qui suit `end` (supprimer la fin)."""
    return text[:end].rstrip()


def rewrite_after(text: str, end: int, new: str) -> str:
    """Remplace tout ce qui suit `end` par `new` (réécrire la fin)."""
    return insert_at(text[:end], end, new)


def changed_span(old: str, new: str) -> tuple[int, int, str]:
    """Plus petite modification qui transforme `old` en `new` : (début, fin, remplacement).

    `old[début:fin]` est remplacé par `remplacement` ; on retire le préfixe et le suffixe communs.
    Les règles d'écriture ajustent les espaces autour d'une modification : elles sont donc
    comprises dans la plage, qui est celle de l'opération et d'elle seule.
    """
    limit = min(len(old), len(new))
    start = 0
    while start < limit and old[start] == new[start]:
        start += 1
    tail = 0
    while tail < limit - start and old[-1 - tail] == new[-1 - tail]:
        tail += 1
    return start, len(old) - tail, new[start : len(new) - tail]
