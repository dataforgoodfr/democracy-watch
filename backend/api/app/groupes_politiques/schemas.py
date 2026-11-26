"""Groupes politiques : sous-type des organes, au-dessus des personnes."""

from pydantic import BaseModel

from ..organes.schemas import Organe


class GroupePolitiqueRef(BaseModel):
    uid: str
    name: str
    short_name: str | None
    color: str | None


class GroupePolitique(Organe):
    color: str | None
    logo_url: str | None
    political_position: str | None
