"""Personnes : bas de la hiérarchie des acteurs, rattachées à leur groupe politique."""

from pydantic import BaseModel

from ..groupes_politiques.schemas import GroupePolitiqueRef


class PersonneRef(BaseModel):
    uid: str  # slug, stable d'un chargement à l'autre
    first_name: str
    last_name: str


class Personne(PersonneRef):
    civility: str | None
    profession: str | None
    photo_url: str | None
    groupe: GroupePolitiqueRef | None  # groupe du mandat en cours
