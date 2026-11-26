"""Amendements : bas de la hiérarchie législative, rattachés à leur article, texte et dossier."""

from datetime import date, datetime

from pydantic import BaseModel

from ..articles.schemas import ArticleRef
from ..dossiers.schemas import DossierRef
from ..groupes_politiques.schemas import GroupePolitiqueRef
from ..organes.schemas import OrganeRef
from ..personnes.schemas import PersonneRef
from ..textes.schemas import TexteRef


class Amendement(BaseModel):
    uid: str
    number: str
    dossier: DossierRef
    texte: TexteRef
    article: ArticleRef | None  # NULL si l'emplacement visé n'a pas été résolu
    targeted_article: str | None  # libellé source, ex. « APRÈS ART. 2 »
    paragraph_number: int | None
    parent_uid: str | None  # sous-amendement : l'amendement visé
    examining_organe: OrganeRef | None  # commission ou séance
    author: PersonneRef | None
    author_organe: OrganeRef | None  # auteur institutionnel : Gouvernement, commission
    groupe: GroupePolitiqueRef | None  # groupe de l'auteur au dépôt
    status: str
    outcome: str | None
    outcome_reason: str | None
    submitted_on: date | None
    outcome_at: datetime | None
    body: str | None  # dispositif
    explanation: str | None  # exposé sommaire
