"""Textes : documents de la navette d'un dossier (projet, proposition, texte adopté…)."""

from datetime import date

from pydantic import BaseModel

from ..dossiers.schemas import DossierRef


class TexteRef(BaseModel):
    uid: str
    nature: str
    number: int | None


class Texte(TexteRef):
    dossier: DossierRef
    chamber: str
    term: int  # législature (AN) ou année de début de session (Sénat)
    position: int  # rang dans le dossier : 1 = premier texte
    title: str | None
    submitted_on: date | None
