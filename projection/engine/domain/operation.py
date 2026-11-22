"""Contrat d'une opération : une donnée immuable qui sait se traduire en patch."""

import copy
from typing import Protocol, Self

from engine.domain.documents import Article
from engine.domain.patch import Patch
from engine.domain.target import Target


class Operation(Protocol):
    """Ce que dit une instruction, indépendamment de sa syntaxe.

    Il y a une opération par famille d'instruction. Le texte cité qu'elles portent est déjà
    normalisé et sans guillemets.
    """

    @property
    def target(self) -> Target:
        """Ce que l'opération vise dans l'article."""
        ...

    def plan(self, article: Article) -> Patch:
        """Patch de l'opération contre `article` (texte d'entrée normalisé) ; lève `Refusal`.

        Les positions de la cible sont celles de `article` : le patch ne dépend d'aucune autre
        opération.
        """
        ...

    def with_target(self, target: Target) -> Operation:
        """La même opération, sur une autre cible (retrouvée dans une autre version)."""
        ...


class Retargetable:
    """Pour les opérations : `with_target`, la même opération sur une autre cible."""

    def with_target(self, target: Target) -> Self:
        """La même opération, sur une autre cible (retrouvée dans une autre version)."""
        return copy.replace(self, target=target)
