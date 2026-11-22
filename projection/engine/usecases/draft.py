"""Brouillon d'un amendement : instructions lues, planifiées contre l'article, pas encore décidées.

Un `Draft` est immuable : les étapes qui suivent (conflits) en rendent un nouveau.
"""

import dataclasses
import re
from collections.abc import Mapping

from engine.domain.documents import Amendment, Article, Text
from engine.domain.normalization import article_number, normalize
from engine.domain.patch import Patch, apply
from engine.domain.refusal import Reason, Refusal
from engine.domain.trace import Instruction, fingerprint
from engine.reading import read
from engine.reading.dispositif import dispositif_lines

_ARTICLE_LABEL = re.compile(r"ART\.\s*(.+)", re.I)
_SEVERAL_ARTICLES = re.compile(r"\b(?:À|ET|OU)\b|[,;]")


def labelled_number(label: str | None) -> str:
    """Numéro de l'article visé : « ART. 5 BIS » → « 5 BIS », « ART. 1ER » → « PREMIER »."""
    if not label:
        raise Refusal(Reason.UNRESOLVED_ARTICLE, "aucun article visé")
    match = _ARTICLE_LABEL.fullmatch(normalize(label).strip())
    if not match:
        # « APRÈS ART. 3 », « TITRE » : pas un article du texte.
        raise Refusal(Reason.OUT_OF_SCOPE, label)
    number = article_number(match[1])
    if _SEVERAL_ARTICLES.search(number):
        # « ART. 3 À 5 », « ART. 3 ET 4 » : plusieurs articles, aucun n'est identifié.
        raise Refusal(Reason.UNRESOLVED_ARTICLE, f"plusieurs articles visés : {label}")
    return number


@dataclasses.dataclass(frozen=True)
class Draft:
    """Un amendement lu et planifié contre son article.

    `article` : l'article de base, alinéas normalisés (None si non résolu) ; `base` : son empreinte
    (`trace.fingerprint`) ; `body` : les lignes du dispositif. `instructions` et `patches` : une
    entrée par instruction, un patch vide pour une instruction refusée. `refusal` : refus de tout
    l'amendement avant ou hors de l'analyse (article inconnu ou hors périmètre).
    """

    amendment: Amendment
    number: str | None = None
    article: Article | None = None
    base: str | None = None
    body: tuple[str, ...] = ()
    instructions: tuple[Instruction, ...] = ()
    patches: tuple[Patch, ...] = ()
    refusal: Refusal | None = None

    @property
    def applicable(self) -> bool:
        """Vrai si l'amendement n'est refusé ni en bloc ni par une de ses instructions."""
        return self.refusal is None and all(i.reason is None for i in self.instructions)

    @property
    def patch(self) -> Patch:
        """Les splices de toutes les instructions, à la suite."""
        return tuple(splice for patch in self.patches for splice in patch)

    def refused(self, refusal: Refusal) -> Draft:
        """Le même brouillon, refusé en bloc : sans instructions, il n'a rien à tracer."""
        return dataclasses.replace(self, refusal=refusal, instructions=(), patches=())

    def with_refusals(self, refusals: Mapping[int, Refusal]) -> Draft:
        """Le même brouillon, dont les instructions d'indice donné sont refusées."""
        instructions = tuple(
            dataclasses.replace(instruction, reason=refusals[k].reason, detail=refusals[k].detail)
            if k in refusals
            else instruction
            for k, instruction in enumerate(self.instructions)
        )
        return dataclasses.replace(self, instructions=instructions)


def _touched(article: Article, patch: Patch) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Alinéas de l'article que le patch touche, avant et après.

    Un alinéa modifié au niveau des caractères compte une fois, avec toutes ses modifications.
    """
    before: list[str] = []
    after: list[str] = []
    seen: set[int] = set()
    for splice in patch:
        if splice.span is None:
            before += article.lines
            after += splice.new
        elif splice.line is None:
            before += article.lines[splice.span[0] : splice.span[1]]
            after += splice.new
        elif splice.line not in seen:
            seen.add(splice.line)
            same_line = tuple(s for s in patch if s.line == splice.line)
            before.append(article.lines[splice.line])
            after.append(apply(article.lines, same_line)[splice.line])
    return tuple(before), tuple(after)


def _plan(instruction: Instruction, article: Article) -> tuple[Instruction, Patch]:
    """L'instruction tracée (avant/après, ou raison du refus) et son patch contre `article`."""
    if instruction.operation is None:
        return instruction, ()
    try:
        patch = instruction.operation.plan(article)
    except Refusal as refusal:
        return dataclasses.replace(instruction, reason=refusal.reason, detail=refusal.detail), ()
    before, after = _touched(article, patch)
    return dataclasses.replace(instruction, before=before, after=after), patch


def draft(text: Text, amendment: Amendment) -> Draft:
    """Lit `amendment` et le planifie contre son article de `text`."""
    number = None
    try:
        number = labelled_number(amendment.target_label)
        found = text.find(number)
    except Refusal as refusal:
        return Draft(amendment, number, refusal=refusal)
    base = fingerprint(text.uid, found)
    try:
        body = dispositif_lines(amendment.body_html)
    except Refusal as refusal:
        return Draft(amendment, number, base=base, refusal=refusal)
    article = dataclasses.replace(found, lines=tuple(normalize(line) for line in found.lines))
    planned = [_plan(instruction, article) for instruction in read(body)]
    return Draft(
        amendment,
        number,
        article,
        base,
        body,
        tuple(instruction for instruction, _ in planned),
        tuple(patch for _, patch in planned),
    )
