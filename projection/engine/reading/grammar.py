"""Grammaires Lark de l'analyse : chargement, analyseur, version."""

import functools
import hashlib
import pathlib

from lark import Lark

_GRAMMAR_DIR = pathlib.Path(__file__).parent / "grammaires"


@functools.cache
def _grammar() -> str:
    """Texte des grammaires : le commun est concaténé devant (pas de %import, voir commun.lark)."""
    return "\n".join(
        (_GRAMMAR_DIR / name).read_text(encoding="utf-8")
        for name in ("commun.lark", "amendements.lark")
    )


def _version(grammar: str) -> str:
    """Empreinte courte d'un texte de grammaire."""
    return hashlib.sha256(grammar.encode()).hexdigest()[:12]


GRAMMAR_VERSION = _version(_grammar())


@functools.cache
def parser() -> Lark:
    """Analyseur Earley des deux points d'entrée (`en_ligne`, `bloc`), ambiguïtés explicites."""
    return Lark(_grammar(), start=["en_ligne", "bloc"], parser="earley", ambiguity="explicit")
