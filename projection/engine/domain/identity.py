"""Identifiants stables : lisibles, déterministes, attribués une fois et jamais recalculés.

Un identifiant désigne un nœud du texte (article, alinéa, mot) indépendamment de sa position : la
numérotation (« alinéa 4 ») se calcule à la demande, l'identifiant ne change pas quand un alinéa
est inséré avant.

Texte d'entrée :  article `UID/5-BIS`, alinéa `UID/5-BIS/a3`, mot `UID/5-BIS/a3/m12`.
Écrit par un amendement : alinéa `AMENDEMENT/a1`, mot `UID/5-BIS/a3/AMENDEMENT.m1`.
Les rangs commencent à 1, comme les numéros d'alinéa des dispositifs.
"""


def article_id(text_uid: str, number: str) -> str:
    """Identifiant d'un article du texte d'entrée : `UID/5-BIS` (les espaces deviennent des `-`)."""
    return f"{text_uid}/{'-'.join(number.split())}"


def paragraph_id(article: str, rank: int) -> str:
    """Identifiant du `rank`-ième alinéa (1 = premier) d'un article du texte d'entrée."""
    return f"{article}/a{rank}"


def word_id(paragraph: str, rank: int) -> str:
    """Identifiant du `rank`-ième mot (1 = premier) d'un alinéa du texte d'entrée."""
    return f"{paragraph}/m{rank}"


def written_paragraph_id(origin: str, rank: int) -> str:
    """Identifiant du `rank`-ième alinéa créé par `origin` (un amendement) dans un article."""
    return f"{origin}/a{rank}"


def written_word_id(paragraph: str, origin: str, rank: int) -> str:
    """Identifiant du `rank`-ième mot que `origin` écrit dans l'alinéa `paragraph`."""
    return f"{paragraph}/{origin}.m{rank}"
