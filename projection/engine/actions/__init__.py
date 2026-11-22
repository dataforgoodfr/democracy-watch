"""Opérations enfichables : chacune sait se traduire en patch (`Operation.plan`).

Ajouter une opération = une classe ici, plus la règle de grammaire qui la construit.
"""

from engine.actions.paragraphs import DeleteNode, InsertNode, Rewrite
from engine.actions.words import (
    DeleteEnd,
    DeleteWords,
    InsertEdge,
    InsertWords,
    RewriteEnd,
    Substitute,
)

__all__ = [
    "DeleteEnd",
    "DeleteNode",
    "DeleteWords",
    "InsertEdge",
    "InsertNode",
    "InsertWords",
    "Rewrite",
    "RewriteEnd",
    "Substitute",
]
