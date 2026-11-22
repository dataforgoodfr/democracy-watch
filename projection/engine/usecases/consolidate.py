"""Consolidation de plusieurs amendements d'une même étape.

Contrat de l'appelant : `text` est le texte OFFICIEL d'entrée de l'étape (la base de la séance
est le texte adopté en commission, jamais notre résultat partiel) et `amendments` les amendements
qu'il a retenus (le moteur ne filtre pas sur le sort).

Chaque amendement est lu seul, comme dans `project`. Les amendements identiques sont fusionnés
Les sous-amendements et leurs parents refusés, puis les patchs des amendements encore
applicables d'un même article sont confrontés par la politique de conflit. Le texte consolidé d'un
article n'est fourni que si tous les amendements qui le visent sont appliqués : un amendement
refusé pourrait le modifier. Un amendement dont l'article visé est inconnu (`UNRESOLVED_ARTICLE`,
`article` None : absent, « ART. 3 À 5 »…) pourrait modifier n'importe quel article : tant qu'il
existe, aucun article n'est consolidé. Les « APRÈS ART. X » (`OUT_OF_SCOPE`) n'ont pas cet effet.
"""

import dataclasses
from collections.abc import Iterable

from engine.domain.documents import Amendment, Text
from engine.domain.grafting import graft
from engine.domain.patch import apply, deletes_article
from engine.domain.refusal import Reason, Refusal
from engine.domain.trace import Consolidation, Projection, Result
from engine.usecases.draft import Draft, draft
from engine.usecases.merge import ConflictPolicy, reject_conflicts
from engine.usecases.project import decide


def _reject_sub_amendments(drafts: list[Draft]) -> list[Draft]:
    """Refuse un sous-amendement et l'amendement qu'il modifie."""
    parents = {d.amendment.parent_id for d in drafts} - {None}
    refused = []
    for item in drafts:
        if item.amendment.parent_id is not None:
            item = item.refused(Refusal(Reason.OUT_OF_SCOPE, "sous-amendement"))
        elif item.amendment.id in parents:
            detail = "amendement ayant un sous-amendement"
            item = item.refused(Refusal(Reason.OUT_OF_SCOPE, detail))
        refused.append(item)
    return refused


def _twins(drafts: list[Draft]) -> dict[int, int]:
    """Pour chaque amendement identique à un précédent : l'indice du premier, qui le représente.

    Identiques : même série (`twin_group`), même article, même dispositif.
    """
    first_of: dict[tuple[str, str | None, tuple[str, ...]], int] = {}
    represented_by: dict[int, int] = {}
    for index, item in enumerate(drafts):
        group = item.amendment.twin_group
        if item.refusal is None and group is not None:
            first = first_of.setdefault((group, item.number, item.body), index)
            if first != index:
                represented_by[index] = first
    return represented_by


def _by_article(drafts: list[Draft], twins: dict[int, int]) -> dict[str, list[int]]:
    """Indices des brouillons applicables et non représentés, par numéro d'article."""
    groups: dict[str, list[int]] = {}
    for index, item in enumerate(drafts):
        if item.number is not None and index not in twins and item.applicable:
            groups.setdefault(item.number, []).append(index)
    return groups


def _article_result(article: str, group: list[Draft]) -> Result:
    """Texte consolidé d'un article : les patchs de tous ses amendements, sur la base commune."""
    patch = tuple(splice for item in group for splice in item.patch)
    assert group[0].article is not None and group[0].tree is not None
    return Result(
        article,
        apply(group[0].article.lines, patch),
        deletes_article(patch),
        graft(group[0].tree, patch, group[0].text_uid).paragraphs,
    )


def consolidate(
    text: Text, amendments: Iterable[Amendment], on_conflict: ConflictPolicy = reject_conflicts
) -> Consolidation:
    """Projette `amendments` sur `text` : une projection par amendement, puis les articles."""
    amendments = tuple(amendments)
    drafts = _reject_sub_amendments([draft(text, amendment) for amendment in amendments])
    twins = _twins(drafts)
    groups = _by_article(drafts, twins)
    for indices in groups.values():
        for index, merged in zip(indices, on_conflict([drafts[i] for i in indices]), strict=True):
            drafts[index] = merged

    projections: list[Projection] = []
    for index, item in enumerate(drafts):
        if index in twins:  # le représentant est avant : sa projection existe déjà
            same = dataclasses.replace(projections[twins[index]], amendment=item.amendment.number)
            projections.append(same)
        else:
            projections.append(decide(item))

    # Cible inconnue : cet amendement pourrait modifier n'importe quel article.
    unlocated = any(
        p.reason is Reason.UNRESOLVED_ARTICLE and p.article is None for p in projections
    )
    articles = []
    for article in () if unlocated else text.articles:
        targeting = [p for p in projections if p.article == article.number]
        if targeting and all(p.applied for p in targeting):
            group = [drafts[i] for i in groups[article.number]]
            articles.append(_article_result(article.number, group))
    return Consolidation(tuple(projections), tuple(articles))
