"""Refus explicite : le moteur ne propose jamais de meilleure hypothèse."""

import enum


class Reason(enum.StrEnum):
    """Raisons de refus typées. La valeur est celle affichée et comptée."""

    AMBIGUOUS = "ambigue"
    OUT_OF_SCOPE = "hors_perimetre"
    TARGET_NOT_FOUND = "cible_introuvable"
    TARGET_GONE = "cible_disparue"
    QUOTE_MISSING = "citation_absente"
    QUOTE_MULTIPLE = "citation_multiple"
    CONFLICT = "conflit"
    INCONSISTENT_BLOCK = "bloc_incoherent"
    UNRESOLVED_ARTICLE = "article_non_resolu"


class Refusal(Exception):
    """Une instruction, un amendement ou un article ne peut pas être traité exactement."""

    def __init__(self, reason: Reason, detail: str = ""):
        super().__init__(f"{reason.value} : {detail}" if detail else reason.value)
        self.reason = reason
        self.detail = detail
