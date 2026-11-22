import pytest

from engine.domain import writing
from engine.domain.refusal import Reason, Refusal
from engine.domain.writing import Anchor


@pytest.mark.parametrize(
    ("texts", "anchor", "expected"),
    [
        (["le chat noir"], Anchor("chat"), (0, 3, 7)),
        (["le chat", "le chien"], Anchor("chien"), (1, 3, 8)),
        # mots entiers : « chat » n'est pas dans « chats »
        (["des chats et un chat"], Anchor("chat"), (0, 16, 20)),
        (["chat chat"], Anchor("chat", 2), (0, 5, 9)),
        (["chat chat"], Anchor("chat", 1), (0, 0, 4)),
        (["chat chat"], Anchor("chat", -1), (0, 5, 9)),
        (["chat", "chat", "chat"], Anchor("chat", -2), (1, 0, 4)),
        (["chat", "chat"], Anchor("chat", 2), (1, 0, 4)),
        # ancres qui commencent ou finissent par un caractère non-mot : pas de frontière de ce côté
        (["x(a)y"], Anchor("(a)"), (0, 1, 4)),
        (["a, et b"], Anchor(", et"), (0, 1, 5)),
        (["a, et b"], Anchor("et "), (0, 3, 6)),
        (["l'été"], Anchor("'été"), (0, 1, 5)),
        # le trait d'union est un caractère de mot, l'apostrophe une frontière
        (["le porte-parole et la porte"], Anchor("porte"), (0, 22, 27)),
        (["porte-parole"], Anchor("porte-parole"), (0, 0, 12)),
        (["l'article 5"], Anchor("article"), (0, 2, 9)),
        # un chiffre ne se trouve pas au milieu d'un nombre décimal
        (["0,5 et 5, puis"], Anchor("5"), (0, 7, 8)),
        (["0,5 et 5"], Anchor("0,5"), (0, 0, 3)),
        # la casse distingue
        (["Le Chat et le chat."], Anchor("chat"), (0, 14, 18)),
        # occurrences non chevauchantes
        (["a---b"], Anchor("--"), (0, 1, 3)),
    ],
)
def test_find_anchor(texts, anchor, expected):
    assert writing.find_anchor(texts, anchor) == expected


@pytest.mark.parametrize(
    ("texts", "anchor", "reason"),
    [
        (["le chat"], Anchor("chien"), Reason.QUOTE_MISSING),
        (["le Chat"], Anchor("chat"), Reason.QUOTE_MISSING),  # sensible à la casse
        (["des chats"], Anchor("chat"), Reason.QUOTE_MISSING),  # mot entier
        (["le chat"], Anchor("le cha"), Reason.QUOTE_MISSING),
        (["le chat"], Anchor("hat"), Reason.QUOTE_MISSING),
        (["chat chat"], Anchor("chat", 3), Reason.QUOTE_MISSING),
        (["chat chat"], Anchor("chat", -3), Reason.QUOTE_MISSING),
        (["chat chat"], Anchor("chat", 0), Reason.QUOTE_MISSING),
        ([], Anchor("chat"), Reason.QUOTE_MISSING),
        (["le porte-parole"], Anchor("porte"), Reason.QUOTE_MISSING),
        (["0,5 et 1.5"], Anchor("5"), Reason.QUOTE_MISSING),
        (["chat chat"], Anchor("chat"), Reason.QUOTE_MULTIPLE),
        (["chat", "chat"], Anchor("chat"), Reason.QUOTE_MULTIPLE),
    ],
)
def test_find_anchor_refuses(texts, anchor, reason):
    with pytest.raises(Refusal) as refusal:
        writing.find_anchor(texts, anchor)
    assert refusal.value.reason is reason


@pytest.mark.parametrize(
    ("text", "point", "new", "expected"),
    [
        ("le chat noir", 7, "gros", "le chat gros noir"),
        ("le chat.", 7, "noir", "le chat noir."),
        ("chat", 0, "le", "le chat"),
        ("le", 2, "chat", "le chat"),
        ("le ", 3, "chat", "le chat"),
        ("le  chat", 3, "gros", "le gros chat"),
        ("", 0, "chat", "chat"),
        # ponctuation collée à gauche
        ("le chat noir", 7, ", gros", "le chat, gros noir"),
        ("le chat noir", 7, ". Gros", "le chat. Gros noir"),
        ("(le chat noir", 8, ")", "(le chat) noir"),
        ("le chat noir", 7, "; gros", "le chat; gros noir"),
        # pas d'espace après une apostrophe, une parenthèse ouvrante, un guillemet ou un tiret
        ("de l'État", 5, "ancien", "de l'ancien État"),
        ("de (État", 4, "l'", "de (l'État"),
        ("a « b", 3, "x", "a «x b"),
        ("un-chat", 3, "x", "un-x chat"),
        ("le chat", 3, "l'", "le l'chat"),
        ("le chat", 3, "(", "le (chat"),
        # ponctuation à droite : pas d'espace ajoutée
        ("le chat, noir", 7, "gros", "le chat gros, noir"),
        ("le chat) noir", 7, "gros", "le chat gros) noir"),
        ("le chat; noir", 7, "gros", "le chat gros; noir"),
    ],
)
def test_insert_at(text, point, new, expected):
    assert writing.insert_at(text, point, new) == expected


@pytest.mark.parametrize(
    ("text", "new", "start", "expected"),
    [
        ("le chat.", "noir", False, "le chat noir."),
        ("le chat;", "noir", False, "le chat noir;"),
        ("le chat :", "noir", False, "le chat noir :"),
        ("le chat", "noir", False, "le chat noir"),
        ("le chat.", ", noir", False, "le chat, noir."),
        ("", "noir", False, "noir"),
        ("du taux ;", "et de X", False, "du taux et de X ;"),
        ("du taux ;", ", x", False, "du taux, x ;"),
        ("du taux :", "x", False, "du taux x :"),
        ("chat noir.", "le", True, "le chat noir."),
        ("chat", ", le", True, ", le chat"),
    ],
)
def test_insert_edge(text, new, start, expected):
    assert writing.insert_edge(text, new, start) == expected


@pytest.mark.parametrize(("text", "new"), [("le chat.", "noir."), ("le chat ;", "noir :")])
def test_insert_edge_refuses_double_final_punctuation(text, new):
    with pytest.raises(Refusal) as refusal:
        writing.insert_edge(text, new, False)
    assert refusal.value.reason is Reason.OUT_OF_SCOPE


@pytest.mark.parametrize(
    ("text", "start", "end", "expected"),
    [
        ("le gros chat", 3, 7, "le chat"),
        ("le chat noir", 7, 12, "le chat"),
        ("le chat, noir", 7, 13, "le chat"),
        ("le chat noir.", 8, 12, "le chat."),
        ("le chat noir, et", 8, 12, "le chat, et"),
        ("le chat noir", 0, 2, "chat noir"),
        ("le chat noir", 3, 12, "le"),
        ("le chat", 0, 7, ""),
        ("un chat noir", 3, 8, "un noir"),
    ],
)
def test_cut(text, start, end, expected):
    assert writing.cut(text, start, end) == expected


@pytest.mark.parametrize(
    ("text", "end", "expected"),
    [
        ("le chat noir.", 7, "le chat"),
        ("le chat noir", 2, "le"),
        ("le chat", 7, "le chat"),
        ("le chat , noir", 8, "le chat"),
    ],
)
def test_cut_after(text, end, expected):
    assert writing.cut_after(text, end) == expected


@pytest.mark.parametrize(
    ("text", "end", "new", "expected"),
    [
        ("le chat noir.", 7, "blanc", "le chat blanc"),
        ("le chat noir.", 7, "blanc.", "le chat blanc."),
        ("le chat noir.", 7, ", blanc.", "le chat, blanc."),
        ("le chat ", 8, "blanc", "le chat blanc"),
        ("le chat noir ;", 7, "blanc ;", "le chat blanc ;"),
    ],
)
def test_rewrite_after(text, end, new, expected):
    assert writing.rewrite_after(text, end, new) == expected


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("Un chat.", "Un rat.", (3, 5, "r")),
        ("Un chat.", "Un chat.", (8, 8, "")),  # aucun changement : insertion vide
        ("a x b", "a b", (2, 4, "")),  # l'espace recollée est dans la plage
        ("abc", "", (0, 3, "")),
        ("", "abc", (0, 0, "abc")),
        ("aXa", "aXXa", (2, 2, "X")),  # le préfixe et le suffixe ne se chevauchent pas
    ],
)
def test_changed_span(old, new, expected):
    start, end, replacement = writing.changed_span(old, new)
    assert (start, end, replacement) == expected
    assert old[:start] + replacement + old[end:] == new
