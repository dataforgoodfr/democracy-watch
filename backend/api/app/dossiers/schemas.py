from datetime import datetime

from pydantic import BaseModel


class Dossier(BaseModel):
    uid: str
    source_uid: str
    title: str
    legislative_term: int
    status: str | None
    procedure: str | None
    submitted_at: datetime | None
    adopted_at: datetime | None
    assembly_url: str | None
    senate_url: str | None
    legifrance_url: str | None
    law_number: str | None
    law_title: str | None
    law_published_at: datetime | None
    subject_uid: str | None
    updated_at: datetime
