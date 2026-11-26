"""Contrat public des parlementaires, sans données personnelles privées."""

from pydantic import BaseModel


class Parliamentarian(BaseModel):
    uid: str
    slug: str
    first_name: str
    last_name: str
    chamber: str
    active: bool
    group_uid: str | None = None
    constituency_uid: str | None = None
    photo_url: str | None = None
    website: str | None = None
