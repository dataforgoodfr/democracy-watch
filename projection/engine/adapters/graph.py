"""Rendu en graphe façon `git log --graph` d'une consolidation (lecture seule, texte brut).

Pour chaque article : le texte de base est le tronc, chaque amendement une branche qui en part
(patch contre la base commune), chaque instruction un commit. Les branches sont fusionnées
dans le résultat si tout s'applique ; `x` marque un refus ou un conflit.

    * base  Article 2 · 2 alinéas
    |\\
    | * 1  (CE1) substituer « annuel » à « semestriel »
    * | x  (CE2) conflit
    |/
    * résultat · 2 alinéas

Usage : `python -m engine.adapters.graph <référence du texte> [<article>]`.
"""

import sys
import textwrap
from collections.abc import Iterator

from engine.domain.refusal import Reason
from engine.domain.trace import Consolidation, Projection

WIDTH = 64  # largeur maximale du libellé d'une instruction


def _label(text: str) -> str:
    """Libellé court sur une ligne."""
    return textwrap.shorten(" ".join(text.split()), WIDTH, placeholder="…")


def _rows(projection: Projection) -> Iterator[tuple[str, str]]:
    """Les commits d'une branche : (marque, libellé) par instruction, ou un seul si refusée."""
    name = f"({projection.amendment})"
    if not projection.instructions:
        yield "x", f"{name} {projection.reason or 'aucune instruction'}"
    for instruction in projection.instructions:
        if instruction.reason is None:
            yield "*", f"{name} {_label(instruction.text)}"
        else:
            yield "x", f"{name} {instruction.reason} : {_label(instruction.text)}"


def _lanes(active: int, count: int, mark: str) -> str:
    """Une ligne de graphe : `mark` dans la colonne `active`, `|` dans les autres."""
    return " ".join(mark if lane == active else "|" for lane in range(count))


def _article(number: str, projections: list[Projection], result_lines: int | None) -> list[str]:
    """Le graphe d'un article : tronc, une branche par amendement, fusion."""
    count = len(projections)
    out = [f"* base  article {number}"]
    if count > 1:
        out.append("|\\" + " \\" * (count - 2))
    for lane, projection in enumerate(projections):
        for mark, label in _rows(projection):
            out.append(f"{_lanes(lane, count, mark)}  {label}")
    if count > 1:
        out.append("|/" + " /" * (count - 2))
    if result_lines is None:
        out.append("o  non consolidé : un amendement est refusé")
    else:
        out.append(f"*  résultat · {result_lines} alinéa(s)")
    return out


def render(consolidation: Consolidation) -> str:
    """Le graphe de tous les articles visés, puis les amendements sans article identifié."""
    results = {result.number: result for result in consolidation.articles}
    by_article: dict[str, list[Projection]] = {}
    unlocated = []
    for projection in consolidation.projections:
        if projection.article is None:
            unlocated.append(projection)
        else:
            by_article.setdefault(projection.article, []).append(projection)

    blocks = []
    for number, projections in by_article.items():
        result = results.get(number)
        blocks.append(_article(number, projections, None if result is None else len(result.lines)))
    if unlocated:
        lines = ["hors article"]
        for projection in unlocated:
            reason = projection.reason or Reason.UNRESOLVED_ARTICLE
            lines.append(f"x  ({projection.amendment}) {reason} : {_label(projection.detail)}")
        blocks.append(lines)
    return "\n\n".join("\n".join(block) for block in blocks)


def main(argv: list[str]) -> None:
    """Consolide les amendements d'un texte Tricoteuses et affiche le graphe (accès réseau)."""
    from datasources import tricoteuses

    from engine.adapters import tricoteuses as adapter
    from engine.usecases import consolidate

    if not 1 <= len(argv) <= 2:
        sys.exit(__doc__)
    source = tricoteuses.read_text(argv[0])
    text = adapter.text_from(source.uid, source.articles)
    amendments = (adapter.amendment_from(a) for a in tricoteuses.text_amendements(argv[0]))
    consolidation = consolidate(text, amendments)
    if len(argv) == 2:
        keep = tuple(p for p in consolidation.projections if p.article == argv[1].upper())
        consolidation = Consolidation(keep, consolidation.articles)
    print(render(consolidation))


if __name__ == "__main__":
    main(sys.argv[1:])
