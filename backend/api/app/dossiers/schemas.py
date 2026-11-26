"""Dossiers : sommet de la hiérarchie législative (dossier > texte > article > amendement)."""

from datetime import date

from pydantic import BaseModel


class DossierRef(BaseModel):
    uid: str
    title: str
    short_title: str | None


class Loi(BaseModel):
    """Loi issue d'un dossier promulgué."""

    number: str | None
    title: str | None
    published_on: date | None
    legifrance_url: str | None


class Dossier(DossierRef):
    procedure: str | None
    procedure_label: str | None
    status: str
    outcome: str | None
    submitted_on: date | None
    outcome_on: date | None
    loi: Loi | None
