"""Sortie du moteur : trace par instruction, résultat, projection, consolidation."""

import dataclasses
import hashlib

from engine.domain.documents import Article
from engine.domain.operation import Operation
from engine.domain.refusal import Reason
from engine.domain.status import Status, status_of
from engine.domain.tree import Paragraph
from engine.domain.version import Version


@dataclasses.dataclass(frozen=True)
class Instruction:
    """Trace d'une instruction : lue, puis appliquée ou refusée avec sa raison."""

    text: str
    operation: Operation | None = None
    reason: Reason | None = None
    detail: str = ""
    before: tuple[str, ...] = ()  # alinéas d'entrée touchés
    after: tuple[str, ...] = ()  # alinéas qui les remplacent


@dataclasses.dataclass(frozen=True)
class Result:
    """Texte résultant d'un article. `deleted` : article supprimé, `lines` est alors vide.

    `paragraphs` : les mêmes alinéas, avec l'identifiant et l'origine de chaque mot ; `lines` en est
    le texte. Ils ne comptent pas dans la comparaison de deux résultats.
    """

    number: str
    lines: tuple[str, ...]
    deleted: bool = False
    paragraphs: tuple[Paragraph, ...] = dataclasses.field(default=(), compare=False)


def fingerprint(text_uid: str, article: Article) -> str:
    """Empreinte de la base d'un patch : l'uid du texte et le contenu de l'article.

    Une projection ne vaut que contre cette base : si l'empreinte change, il faut réévaluer.
    """
    content = "\x00".join((text_uid, article.number, *article.lines))
    return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclasses.dataclass(frozen=True)
class Projection:
    """Sortie du moteur pour un amendement : un résultat exact, ou un refus tracé.

    `base` : empreinte de l'article de base (voir `fingerprint`), None si l'article est inconnu.
    """

    amendment: str  # numéro de l'amendement, pour l'affichage
    article: str | None
    result: Result | None
    reason: Reason | None
    detail: str
    instructions: tuple[Instruction, ...]
    grammar_version: str
    base: str | None = None
    decided_at: str | None = None  # date de la décision de l'amendement, si connue
    forced: Status | None = None  # statut imposé par la consolidation, sinon déduit de `reason`

    @property
    def applied(self) -> bool:
        """Vrai si l'amendement est appliqué (un résultat, pas de refus)."""
        return self.result is not None

    @property
    def status(self) -> Status:
        """Statut imposé par la consolidation, sinon déduit de la raison de refus."""
        return self.forced or status_of(self.reason, self.result)


@dataclasses.dataclass(frozen=True)
class Consolidation:
    """Sortie du moteur pour plusieurs amendements d'une même étape.

    `projections` : une par amendement, dans l'ordre d'entrée. `articles` : texte consolidé des
    articles dont tous les amendements sont appliqués, dans l'ordre du texte d'entrée. `version` :
    le texte de l'étape avec ces articles consolidés ; les autres y sont tels que le texte d'entrée
    les donne, donc exacts seulement pour les articles de `articles`.
    """

    projections: tuple[Projection, ...]
    articles: tuple[Result, ...]
    version: Version
