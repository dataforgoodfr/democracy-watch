"""Découpage d'un dispositif en instructions et extraction des blocs cités."""

import re

from engine.domain.refusal import Reason, Refusal

_MARKER = re.compile(r"([IVXLC]+)\.\s*[–—-]\s*")
_ROMAN = (
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)
_CLOSING = re.compile(r"»\s*[.;]?$")


def _roman(number: int) -> str:
    result = ""
    for value, symbol in _ROMAN:
        while number >= value:
            result += symbol
            number -= value
    return result


def split_units(lines: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Découpe les lignes en unités d'instruction.

    Si la première ligne commence par un marqueur « I. – », chaque marqueur ouvre une
    unité, marqueur retiré ; ils doivent se suivre (I, II, III…). Sinon, une seule unité.
    """
    if not lines:
        raise Refusal(Reason.OUT_OF_SCOPE, "dispositif vide")
    if not _MARKER.match(lines[0]):
        return (lines,)
    units: list[list[str]] = []
    for line in lines:
        marker = _MARKER.match(line)
        if marker is None:
            units[-1].append(line)
            continue
        if marker.group(1) != _roman(len(units) + 1):
            raise Refusal(Reason.AMBIGUOUS, f"marqueur « {marker.group(1)}. » hors suite")
        rest = line[marker.end() :].strip()
        units.append([rest] if rest else [])
    return tuple(tuple(unit) for unit in units)


def block_citations(lines: tuple[str, ...]) -> tuple[str, ...]:
    """Texte des alinéas d'un bloc cité : sans le « ouvrant ni le » final.

    Une ponctuation `.` ou `;` après le » final appartient à l'instruction et est retirée.
    """
    if not lines:
        raise Refusal(Reason.INCONSISTENT_BLOCK, "bloc vide")
    texts = []
    for index, line in enumerate(lines):
        line = line.strip()
        if not line.startswith("«"):
            raise Refusal(Reason.INCONSISTENT_BLOCK, f"alinéa sans « ouvrant : {line}")
        if index < len(lines) - 1:
            if line.endswith("»"):
                raise Refusal(Reason.INCONSISTENT_BLOCK, f"» avant la fin du bloc : {line}")
        elif _CLOSING.search(line) is None:
            raise Refusal(Reason.INCONSISTENT_BLOCK, "dernier alinéa sans » final")
        else:
            line = _CLOSING.sub("", line)
        text = line[1:].strip()
        if not text:
            raise Refusal(Reason.INCONSISTENT_BLOCK, "alinéa cité vide")
        texts.append(text)
    return tuple(texts)
