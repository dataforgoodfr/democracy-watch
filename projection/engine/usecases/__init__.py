"""Cas d'usage du moteur : `project` (un amendement) et `consolidate` (une étape)."""

from engine.usecases.consolidate import consolidate
from engine.usecases.project import project

__all__ = ["consolidate", "project"]
