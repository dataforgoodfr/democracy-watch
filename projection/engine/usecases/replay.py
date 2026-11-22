"""Rejeu : appliquer un amendement sur la version courante du texte.

L'ordre des amendements est celui que fournit l'appelant : ce module n'ordonne rien.

Un patch n'a de sens que contre sa base : on ne décale jamais ses positions. L'amendement est
relu contre la version courante. Le numéro d'alinéa se lit dans la version de référence et se
retrouve par identifiant ; les mots cités se cherchent dans l'alinéa tel qu'il est maintenant.
Ce qui était là dans la référence et n'y est plus (alinéa réécrit, mots retirés par un amendement
adopté plus tôt) est `TARGET_GONE` : l'amendement est tombé, il n'est pas appliqué à côté.
Une insertion fait exception : elle ne dépend que de l'endroit de l'alinéa visé, pas de son texte
(voir `remap_insertion`).
"""

import dataclasses
import itertools

from engine.actions.paragraphs import InsertNode
from engine.domain.documents import Article
from engine.domain.effect import Effect, effect_of
from engine.domain.grafting import graft
from engine.domain.operation import Operation
from engine.domain.patch import Patch, apply, conflicts, deletes_article
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import remap, remap_insertion
from engine.domain.version import Version
from engine.usecases.draft import Draft


def _plan(moved: Operation, current: Article) -> Patch:
    """Patch de `moved` contre la version courante ; une citation absente est « disparue ».

    L'amendement a été lu sans refus sur le texte d'entrée : si ses mots cités ne sont plus dans
    l'alinéa, c'est qu'un amendement adopté plus tôt les a retirés ou réécrits.
    """
    try:
        return moved.plan(current)
    except Refusal as refusal:
        if refusal.reason is Reason.QUOTE_MISSING:
            raise Refusal(Reason.TARGET_GONE, refusal.detail) from None
        raise


def replay(version: Version, reference: Version, draft: Draft) -> tuple[Version, Effect]:
    """La version après `draft`, et son effet ; `Refusal` si l'amendement ne s'y applique pas.

    `reference` : la version d'origine, où sont lus les numéros d'alinéa. Tout ou rien : une
    instruction refusée refuse tout l'amendement, et `version` reste inchangée.
    """
    if draft.refusal is not None:
        raise draft.refusal
    refused = next((i for i in draft.instructions if i.reason is not None), None)
    if refused is not None and refused.reason is not None:
        raise Refusal(refused.reason, refused.detail)
    if draft.number is None:
        raise Refusal(Reason.UNRESOLVED_ARTICLE, "aucun article visé")
    origin = draft.amendment.id or draft.amendment.number
    ref_tree, current = reference.find(draft.number), version.find(draft.number)
    view = Article(current.number, current.lines)
    patches = []
    for instruction in draft.instructions:
        operation = instruction.operation
        assert operation is not None
        if isinstance(operation, InsertNode):
            target, after = remap_insertion(operation.target, ref_tree, current, operation.after)
            moved = dataclasses.replace(operation, target=target, after=after)
        else:
            moved = operation.with_target(remap(operation.target, ref_tree, current))
        patch = _plan(moved, view)
        patches.append(tuple(dataclasses.replace(s, origin=origin) for s in patch))
    for a, b in itertools.combinations(patches, 2):
        if any(conflicts(x, y) for x in a for y in b):
            raise Refusal(Reason.CONFLICT, "instructions non disjointes")
    patch = tuple(splice for part in patches for splice in part)
    if patch and not apply(view.lines, patch) and not deletes_article(patch):
        raise Refusal(Reason.OUT_OF_SCOPE, "tous les alinéas supprimés : supprimer l'article")
    return version.replace(graft(current, patch, version.text_uid), origin), effect_of(
        current, patch
    )
