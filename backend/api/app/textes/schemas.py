"""Un texte est exposé au niveau article : une ligne par article CLAIR."""

from pydantic import BaseModel


class Text(BaseModel):
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
