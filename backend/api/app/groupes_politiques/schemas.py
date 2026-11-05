"""Contrat public des groupes politiques."""

from pydantic import BaseModel


class PoliticalGroup(BaseModel):
    uid: str
    slug: str
    name: str
    chamber: str
    active: bool
    full_name: str | None = None
    short_name: str | None = None
    color: str | None = None
    political_position: str | None = None
    legislative_term: int | None = None
    active_member_count: int | None = None
