"""Modèle Article et adaptateur de lecture des articles depuis la base CLAIR (canutes)."""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Any

_BLOCK_TAGS = frozenset({"p", "div", "li"})
_HTML_HINT_RE = re.compile(r"<(?:p|div|li|br|span)\b", re.IGNORECASE)
_SPACE_RE = re.compile(r"\s+")
_GLUED_ALINEA_RE = re.compile(r'(?:^|(?<=[\s\.\;\:\!\?]))(?P<num>\d{1,3})(?=[A-ZÀ-ÖØ-Þ«"(])')
_LINE_ALINEA_RE = re.compile(r"(?m)^\s*(?P<num>\d{1,3})(?:[.)]|\s+)(?=\S)")
_LEADING_ALINEA_RE = re.compile(
    r"^\s*(?P<num>\d{1,3})(?:[.)]\s*|\s+(?=[^\d\-])|(?=[A-ZÀ-ÖØ-Þ«\"(]))"
)


@dataclass(frozen=True, slots=True)
class Alinea:
    """Alinéa numéroté d'un article."""

    number: int
    text: str


@dataclass(frozen=True, slots=True)
class Article:
    """Contrat public d'un article issu de la dernière version du texte d'un dossier."""

    uid: str
    text_ref: str
    number: str
    title: str
    alineas: tuple[Alinea, ...]
    content: str
    order: int
    dossier_uid: str | None = None
    dossier_title: str | None = None
    dossier_type: str | None = None
    dossier_commission: str | None = None
    dossier_stage: str | None = None
    source_url: str | None = None


class _BlockHTMLParser(HTMLParser):
    """Extrait les paragraphes HTML (<p>, <div>, <li>) en texte normalisé."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._current: list[str] = []
        self._in_block = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        if name in _BLOCK_TAGS:
            self._flush()
            self._in_block = True
        elif name == "br":
            self._current.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self._flush()
            self._in_block = False

    def handle_data(self, data: str) -> None:
        self._current.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        raw = "".join(self._current)
        self._current.clear()
        text = _normalize_spaces(unescape(raw))
        if text:
            self.blocks.append(text)


def _normalize_spaces(text: str) -> str:
    return _SPACE_RE.sub(" ", text).strip()


def _split_html_alineas(content: str) -> tuple[Alinea, ...]:
    parser = _BlockHTMLParser()
    parser.feed(content)
    parser.close()
    blocks = parser.blocks
    if not blocks:
        return ()

    alineas: list[Alinea] = []
    expected = 1
    for block in blocks:
        match = _LEADING_ALINEA_RE.match(block)
        if match and int(match.group("num")) == expected:
            body = block[match.end() :].strip()
            alineas.append(Alinea(number=expected, text=body or block))
            expected += 1
        elif len(blocks) > 1:
            alineas.append(Alinea(number=expected, text=block))
            expected += 1
        else:
            return _split_plain_alineas(block)
    return tuple(alineas)


def _split_plain_alineas(content: str) -> tuple[Alinea, ...]:
    cleaned = content.strip()
    if not cleaned:
        return ()

    candidates: list[tuple[int, int, int]] = []
    for pattern in (_GLUED_ALINEA_RE, _LINE_ALINEA_RE):
        for match in pattern.finditer(cleaned):
            candidates.append((match.start(), match.end(), int(match.group("num"))))
    candidates.sort(key=lambda item: item[0])

    splits: list[tuple[int, int, int]] = []
    expected = 1
    last_end = -1
    for start, end, num in candidates:
        if start < last_end or num != expected:
            continue
        splits.append((start, end, num))
        last_end = end
        expected += 1

    if not splits:
        return (Alinea(number=1, text=_normalize_spaces(cleaned)),)

    alineas: list[Alinea] = []
    for index, (start, end, num) in enumerate(splits):
        next_start = splits[index + 1][0] if index + 1 < len(splits) else len(cleaned)
        if index == 0 and start > 0:
            prefix = _normalize_spaces(cleaned[:start])
            if prefix:
                alineas.append(Alinea(number=0, text=prefix))
        segment = _normalize_spaces(cleaned[end:next_start])
        if segment:
            alineas.append(Alinea(number=num, text=segment))
    return tuple(alineas)


def split_alineas(content: str) -> tuple[Alinea, ...]:
    """Découpe le contenu d'un article (HTML ou texte brut canutes) en alinéas numérotés."""
    if not content or not content.strip():
        return ()
    if _HTML_HINT_RE.search(content):
        parsed = _split_html_alineas(content)
        if parsed:
            return parsed
    return _split_plain_alineas(content)


def _infer_dossier_type(
    procedure_code: str | None,
    procedure_libelle: str | None,
    dossier_title: str | None,
) -> str | None:
    haystack = " ".join(
        part for part in (procedure_code, procedure_libelle, dossier_title) if part
    ).lower()
    if not haystack:
        return None
    if "proposition de loi" in haystack or "ppl" in haystack:
        return "PPL"
    if "projet de loi" in haystack or "pjl" in haystack:
        return "PJL"
    return None


def _row_to_article(row: dict[str, Any]) -> Article:
    """Convertit une ligne CLAIR en objet Article du domaine."""
    raw_content = row.get("contenu") or ""
    return Article(
        uid=str(row["id"]),
        text_ref=str(row["texte_ref"]),
        number=str(row["numero"]),
        title=str(row["libelle"]),
        alineas=split_alineas(raw_content),
        content=_normalize_spaces(unescape(re.sub(r"<[^>]+>", " ", raw_content))),
        order=int(row["ordre"]),
        dossier_uid=row.get("dossier_id"),
        dossier_title=row.get("dossier_titre"),
        dossier_type=_infer_dossier_type(
            row.get("dossier_procedure_code"),
            row.get("dossier_procedure_libelle"),
            row.get("dossier_titre"),
        ),
        dossier_commission=row.get("dossier_commission"),
        dossier_stage=row.get("dossier_etat"),
        source_url=row.get("source_url"),
    )


_LATEST_ARTICLES_SQL = """
WITH latest_textes AS (
    SELECT DISTINCT ON (ta.dossier_id)
        ta.dossier_id,
        ta.texte_ref
    FROM textes_articles ta
    WHERE ta.legislature = %s
      AND ta.dossier_id IS NOT NULL
    GROUP BY ta.dossier_id, ta.texte_ref
    ORDER BY ta.dossier_id, MAX(ta.updated_at) DESC, ta.texte_ref DESC
),
primary_commission AS (
    SELECT DISTINCT ON (dc.dossier_id)
        dc.dossier_id,
        c.nom AS commission_nom
    FROM dossier_commissions dc
    JOIN commissions c ON c.id = dc.commission_id
    ORDER BY
        dc.dossier_id,
        CASE WHEN LOWER(dc.role) LIKE '%%fond%%' THEN 0 ELSE 1 END,
        dc.role
)
SELECT
    ta.id,
    ta.texte_ref,
    ta.numero,
    ta.libelle,
    ta.ordre,
    ta.contenu,
    ta.dossier_id,
    ta.source_url,
    dl.titre AS dossier_titre,
    dl.procedure_code AS dossier_procedure_code,
    dl.procedure_libelle AS dossier_procedure_libelle,
    dl.etat AS dossier_etat,
    pc.commission_nom AS dossier_commission
FROM textes_articles ta
LEFT JOIN latest_textes lt
    ON lt.dossier_id = ta.dossier_id
LEFT JOIN dossiers_legislatifs dl
    ON dl.id = ta.dossier_id
LEFT JOIN primary_commission pc
    ON pc.dossier_id = ta.dossier_id
WHERE ta.legislature = %s
  AND (ta.dossier_id IS NULL OR ta.texte_ref = lt.texte_ref)
ORDER BY ta.dossier_id NULLS LAST, ta.texte_ref, ta.ordre, ta.id
"""


def iter_articles(conn: Any, legislature: int = 17) -> Iterator[Article]:
    """Itère les articles de la dernière version du texte de chaque dossier pour une législature."""
    with conn.cursor() as cur:
        cur.execute(_LATEST_ARTICLES_SQL, (legislature, legislature))
        for row in cur:
            yield _row_to_article(row)
