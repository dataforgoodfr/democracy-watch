"""Métadonnées publiques des déclarations HATVP, sans contenu XML."""

from datetime import datetime

from pydantic import BaseModel


class HatvpDeclaration(BaseModel):
    uid: str
    parliamentarian_uid: str
    document_type: str
    submitted_at: datetime | None = None
    published_at: datetime | None = None
    status: str | None = None
    dossier_url: str | None = None
