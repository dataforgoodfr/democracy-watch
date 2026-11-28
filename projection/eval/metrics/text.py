"""Préparation des textes avant comparaison : normalisation et découpage en mots."""

import re
import unicodedata

# Variantes typographiques ramenées à une seule forme, par point de code : les sources ne les
# écrivent pas toutes pareil. La casse et la numérotation sont gardées : elles changent le sens.
TYPOGRAPHY = str.maketrans(
    {
        **dict.fromkeys(map(chr, (0x00A0, 0x202F, 0x2009)), " "),  # espaces insécables et fines
        **dict.fromkeys(map(chr, (0x2018, 0x2019)), "'"),  # apostrophes typographiques
        **dict.fromkeys(map(chr, (0x00AB, 0x00BB, 0x201C, 0x201D)), '"'),  # guillemets
        **dict.fromkeys(map(chr, (0x2011, 0x2013, 0x2014)), "-"),  # tirets
    }
)
TOKEN = re.compile(r"\w+|[^\w\s]")  # un mot, ou un signe de ponctuation


def normalize(text: str) -> str:
    """Texte comparable : forme Unicode NFC, typographie unifiée, blancs réduits à un espace."""
    return " ".join(unicodedata.normalize("NFC", text).translate(TYPOGRAPHY).split())


def tokens(text: str) -> list[str]:
    """Mots et signes de ponctuation du texte normalisé."""
    return TOKEN.findall(normalize(text))
