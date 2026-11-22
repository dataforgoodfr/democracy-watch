"""Lecture : du texte d'un dispositif aux opérations. Seul `read` est public."""

from engine.reading.grammar import GRAMMAR_VERSION
from engine.reading.reader import read

__all__ = ["GRAMMAR_VERSION", "read"]
