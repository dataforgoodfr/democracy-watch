"""Historique entre étapes : retrouver, dans le texte d'une étape, d'où viennent ses mots.

Le texte d'entrée de la séance est le texte OFFICIEL adopté en commission, jamais notre résultat :
ses mots n'ont donc aucun lien avec ceux que nous avons projetés. `link` les rattache en alignant,
article par article puis alinéa par alinéa, le texte projeté de l'étape précédente et le nouveau
texte. Un mot rattaché garde tout son parcours (`Word.trail`) : l'amendement qui l'a écrit, puis les
textes successifs par lesquels il est passé.

On ne devine pas : seuls des passages identiques sont rattachés. Un passage trop court pour être
sûr, ou qui se retrouve à plusieurs endroits (« de la loi » dit deux fois), ne l'est jamais. Un mot
sans correspondant est une retouche du texte officiel, absente des amendements : il naît dans le
nouveau texte. Un rattachement qui ne vient pas d'un alinéa strictement identique est marqué
`approximate`.
"""

import dataclasses
import difflib
from collections import Counter

from engine.domain.documents import Text
from engine.domain.tree import ArticleTree, Origin, Paragraph, Word
from engine.domain.version import Version

MIN_WORDS = 4  # dans un alinéa modifié, un passage commun doit porter au moins quatre vrais mots


def _is_word(word: Word) -> bool:
    return any(char.isalnum() for char in word.text)


def _occurrences(tokens: list[str], block: list[str]) -> int:
    """Combien de fois la suite `block` apparaît dans `tokens`."""
    return sum(tokens[k : k + len(block)] == block for k in range(len(tokens) - len(block) + 1))


def _carried(old: Word, new: Word, text_uid: str, approximate: bool) -> Word:
    """`new`, avec le parcours de `old` : son origine devient un événement de l'historique."""
    return Word(new.id, new.text, Origin(text_uid, None, approximate), old.trail)


def _link_paragraph(old: Paragraph, new: Paragraph, text_uid: str, exact: bool) -> Paragraph:
    """Le paragraphe `new`, dont les mots passés sous silence par `old` gardent leur parcours."""
    if old.text == new.text:
        words = tuple(
            _carried(o, n, text_uid, not exact) for o, n in zip(old.words, new.words, strict=True)
        )
        return Paragraph(new.id, words)
    words = list(new.words)
    before, after = [w.text for w in old.words], [w.text for w in new.words]
    for i, j, size in difflib.SequenceMatcher(
        None, before, after, autojunk=False
    ).get_matching_blocks():
        block = after[j : j + size]
        if sum(_is_word(w) for w in new.words[j : j + size]) < MIN_WORDS:
            continue  # trop court pour être sûr (et on évite de le chercher)
        if _occurrences(before, block) == 1 and _occurrences(after, block) == 1:
            for k in range(size):
                words[j + k] = _carried(old.words[i + k], new.words[j + k], text_uid, True)
    return Paragraph(new.id, tuple(words))


def _link_article(old: ArticleTree, new: ArticleTree, text_uid: str) -> ArticleTree:
    """Alinéas identiques rattachés mot à mot ; alinéas modifiés rattachés s'ils se correspondent.

    Deux séries d'alinéas de même longueur qui diffèrent se correspondent position à position
    (approximatif) ; sinon on ne rattache rien : aucun alinéa n'est apparié au hasard.
    """
    matcher = difflib.SequenceMatcher(None, old.lines, new.lines, autojunk=False)
    paragraphs = list(new.paragraphs)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(j2 - j1):
                line = new.lines[j1 + k]
                unique = old.lines.count(line) == 1 and new.lines.count(line) == 1
                paragraphs[j1 + k] = _link_paragraph(
                    old.paragraphs[i1 + k],
                    new.paragraphs[j1 + k],
                    text_uid,
                    tag == "equal" and unique,
                )
    return dataclasses.replace(new, paragraphs=tuple(paragraphs))


def link(previous: Version, text: Text) -> Version:
    """La version d'origine de `text`, dont les mots portent leur parcours depuis `previous`.

    `previous` : le texte projeté de l'étape qui précède (par exemple `Consolidation.version`) ;
    `text` : le texte d'entrée officiel de l'étape suivante. Les articles sont appariés par numéro,
    s'il est unique des deux côtés.
    """
    version = Version.of(text)
    counts = Counter(a.number for a in (*previous.articles, *version.articles))
    before = {a.number: a for a in previous.articles}
    articles = tuple(
        _link_article(before[a.number], a, text.uid)
        if a.number in before and counts[a.number] == 2
        else a
        for a in version.articles
    )
    return dataclasses.replace(version, articles=articles)
