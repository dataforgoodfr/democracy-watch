"""Normalisation du texte : appliquée à l'identique à l'article et au dispositif."""

import re

CHARACTERS = str.maketrans(
    {
        " ": " ",  # espace insécable
        " ": " ",  # espace fine insécable
        "‑": "-",  # trait d'union insécable
        "’": "'",  # apostrophe typographique
    }
)


def normalize(text: str) -> str:
    """Table unique de normalisation ; ne retire pas les espaces des bords du texte."""
    text = text.translate(CHARACTERS)
    text = re.sub(r"«\s+", "«", text)
    return re.sub(r"\s+»", "»", text)


def article_number(text: str) -> str:
    """Numéro d'article normalisé : majuscules, espaces simples, « 1er » devenu « PREMIER »."""
    number = " ".join(text.upper().split())
    return "PREMIER" if number in ("1ER", "1 ER") else number
