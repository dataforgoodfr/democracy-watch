"""Organes : sommet de la hiérarchie des acteurs (organe > groupe politique > personne)."""

from datetime import date

from pydantic import BaseModel


class TypeOrgane(BaseModel):
    """Référentiel à part, hors hiérarchie : sert de filtre aux organes."""

    code: str
    label: str
    family: str
    chamber: str | None


class OrganeRef(BaseModel):
    uid: str
    type: str
    name: str
    short_name: str | None


class Organe(OrganeRef):
    type_label: str
    family: str
    chamber: str | None
    parent_uid: str | None
    start_date: date | None
    end_date: date | None
