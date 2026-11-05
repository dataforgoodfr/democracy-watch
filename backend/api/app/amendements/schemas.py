from datetime import datetime

from pydantic import BaseModel


class Amendement(BaseModel):
    uid: str
    source_uid: str
    number: str
    chamber: str
    legislative_term: int
    targeted_article: str | None
    body: str | None
    explanation: str | None
    outcome: str | None
    submitted_at: datetime | None
    author: str | None
    text_reference: str | None
    dossier_uid: str | None
    parliamentarian_uid: str | None
    group_reference: str | None
    author_reference: str | None
    paragraph: str | None
    paragraph_number: int | None
    order_number: int | None
    parent_amendement_uid: str | None
    sitting_reference: str | None
    joint_discussion_id: str | None
    identical_discussion_id: str | None
