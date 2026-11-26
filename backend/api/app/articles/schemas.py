"""Contrat public des articles, indépendant du stockage CLAIR."""

from pydantic import BaseModel


class Article(BaseModel):
    uid: str
    text_reference: str
    number: str
    label: str
    content: str
    position: int
    chamber: str
    legislative_term: int
    dossier_uid: str | None
    source_url: str | None
