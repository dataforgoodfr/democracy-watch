"""Dispositif HTML → lignes de texte."""

import html
import re

from engine.domain.normalization import CHARACTERS, normalize
from engine.domain.refusal import Reason, Refusal

_PARAGRAPH = re.compile(r"<p\b[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)
_BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]*>")


def dispositif_lines(markup: str) -> tuple[str, ...]:
    """Lignes d'un dispositif HTML : un `<p>` = une ligne, sans ligne vide.

    Les `<br>` valent une espace et les autres balises en ligne sont retirées avant que les
    entités soient déséchappées. Lève `Refusal(OUT_OF_SCOPE)` si du contenu (texte ou balise de
    bloc) se trouve hors des `<p>` : le cas d'usage l'attrape et refuse le dispositif.
    """
    outside = _PARAGRAPH.sub("", markup)
    if _TAG.search(outside) or html.unescape(outside).translate(CHARACTERS).strip():
        raise Refusal(Reason.OUT_OF_SCOPE, "contenu hors des paragraphes")
    paragraphs = (_TAG.sub("", _BREAK.sub(" ", p)) for p in _PARAGRAPH.findall(markup))
    lines = (normalize(html.unescape(p)).strip() for p in paragraphs)
    return tuple(line for line in lines if line)
