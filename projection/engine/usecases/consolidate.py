"""Consolidation de plusieurs amendements d'une même étape.

Contrat de l'appelant : `text` est le texte OFFICIEL d'entrée de l'étape (la base de la séance
est le texte adopté en commission, jamais notre résultat partiel) et `amendments` les amendements
qu'il a retenus (le moteur ne filtre pas sur le sort).

Chaque amendement est lu seul, comme dans `project`. Les amendements identiques sont fusionnés
Les sous-amendements et leurs parents refusés, puis les patchs des amendements encore
applicables d'un même article sont confrontés par la politique de conflit (par défaut, la décision
la plus ancienne l'emporte). Les amendements applicables d'un article sont ensuite rejoués dans
l'ordre sur la version d'origine (`replay`) : le texte consolidé de l'article est lu dans cette
version. Il n'est fourni que si tous les amendements qui le visent sont appliqués : un amendement
refusé pourrait le modifier. Un amendement dont l'article visé est inconnu (`UNRESOLVED_ARTICLE`,
`article` None : absent, « ART. 3 À 5 »…) pourrait modifier n'importe quel article : tant qu'il
existe, aucun article n'est consolidé. Les « APRÈS ART. X » (`OUT_OF_SCOPE`) n'ont pas cet effet.
"""

import dataclasses
from collections.abc import Iterable

from engine.domain.documents import Amendment, Text
from engine.domain.refusal import Reason, Refusal
from engine.domain.trace import Consolidation, Projection, Result
from engine.domain.tree import ArticleTree
from engine.domain.version import Version
from engine.usecases.draft import Draft, draft
from engine.usecases.merge import ConflictPolicy, oldest_wins
from engine.usecases.project import decide
from engine.usecases.replay import replay


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


def _article_result(tree: ArticleTree) -> Result:
    """Texte consolidé d'un article, lu dans sa version rejouée. Sans alinéa : article supprimé."""
    return Result(tree.number, tree.lines, not tree.paragraphs, tree.paragraphs)


def consolidate(
    text: Text, amendments: Iterable[Amendment], on_conflict: ConflictPolicy = oldest_wins
) -> Consolidation:
    """Projette `amendments` sur `text` : une projection par amendement, puis les articles."""
    amendments = tuple(amendments)
    drafts = _reject_sub_amendments([draft(text, amendment) for amendment in amendments])
    twins = _twins(drafts)
    groups = _by_article(drafts, twins)
    for indices in groups.values():
        for index, merged in zip(indices, on_conflict([drafts[i] for i in indices]), strict=True):
            drafts[index] = merged

    reference = Version.of(text)
    replayed: dict[str, Version] = {}
    for number, indices in groups.items():
        current = reference
        for index in (i for i in indices if drafts[i].applicable):
            try:
                current, _ = replay(current, reference, drafts[index])
            except Refusal as refusal:
                drafts[index] = drafts[index].refused(refusal)
        replayed[number] = current

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
    version = reference
    for article in () if unlocated else text.articles:
        targeting = [p for p in projections if p.article == article.number]
        if targeting and all(p.applied for p in targeting):
            tree = replayed[article.number].find(article.number)
            articles.append(_article_result(tree))
            group = (drafts[i].amendment for i in groups[article.number])
            version = version.replace(tree, *(a.id or a.number for a in group))
    return Consolidation(tuple(projections), tuple(articles), version)
