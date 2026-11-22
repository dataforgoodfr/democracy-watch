import pytest

from engine.domain.patch import Splice, apply, conflicts, deletes_article


def edit(start, end, new):
    return Splice.on_lines("5", start, end, new)


def article_edit(new):
    return Splice.on_article("5", new)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        # insertions
        (edit(2, 2, ("x",)), edit(2, 2, ("y",)), True),
        (edit(2, 2, ("x",)), edit(3, 3, ("y",)), False),
        (edit(1, 1, ("x",)), edit(1, 1, ("y",)), True),
        # insertion dans une plage
        (edit(2, 2, ("x",)), edit(1, 3, ("y",)), True),
        (edit(1, 3, ("y",)), edit(2, 2, ("x",)), True),
        # insertion sur les bords d'une plage : pas de conflit
        (edit(1, 1, ("x",)), edit(1, 3, ("y",)), False),
        (edit(3, 3, ("x",)), edit(1, 3, ("y",)), False),
        (edit(1, 3, ("y",)), edit(3, 3, ("x",)), False),
        (edit(1, 3, ("y",)), edit(1, 1, ("x",)), False),
        # plages
        (edit(1, 3, ("x",)), edit(2, 4, ("y",)), True),
        (edit(2, 4, ("x",)), edit(1, 3, ("y",)), True),
        (edit(1, 4, ("x",)), edit(2, 3, ("y",)), True),
        (edit(1, 3, ("x",)), edit(1, 3, ("y",)), True),
        (edit(1, 2, ("x",)), edit(2, 3, ("y",)), False),
        (edit(1, 2, ("x",)), edit(4, 5, ("y",)), False),
    ],
)
def test_conflicts(a, b, expected):
    assert conflicts(a, b) is expected


@pytest.mark.parametrize(
    ("edits", "expected"),
    [
        ((), ("a", "b", "c")),
        ((edit(1, 2, ("B",)),), ("a", "B", "c")),
        ((edit(1, 2, ()),), ("a", "c")),
        ((edit(0, 0, ("x",)),), ("x", "a", "b", "c")),
        ((edit(3, 3, ("x",)),), ("a", "b", "c", "x")),
        # positions d'origine, quel que soit l'ordre des Edit
        ((edit(2, 3, ("C",)), edit(0, 1, ("A", "A2"))), ("A", "A2", "b", "C")),
        ((edit(2, 2, ("x",)), edit(0, 1, ())), ("b", "x", "c")),
        ((edit(0, 1, ("x",)), edit(1, 2, ("y",))), ("x", "y", "c")),
        # une insertion précède un remplacement de même début
        ((edit(1, 2, ("B",)), edit(1, 1, ("x",))), ("a", "x", "B", "c")),
        (
            (
                edit(
                    0,
                    3,
                    ("Z",),
                ),
            ),
            ("Z",),
        ),
        ((article_edit(()),), ()),
    ],
)
def test_apply(edits, expected):
    assert apply(("a", "b", "c"), edits) == expected


def test_article_deletion_conflicts_with_touching_insertion():
    deletion = article_edit(())
    assert conflicts(deletion, edit(0, 0, ("x",)))
    assert conflicts(edit(3, 3, ("x",)), deletion)


@pytest.mark.parametrize(
    "other", [edit(0, 0, ("x",)), edit(3, 3, ("x",)), edit(1, 2, ("x",))], ids=str
)
def test_article_rewrite_conflicts_with_any_other_edit(other):
    rewrite = article_edit(("Nouveau.",))
    assert conflicts(rewrite, other) and conflicts(other, rewrite)


def test_deletes_article_only_without_new_text():
    assert deletes_article((article_edit(()),))
    assert not deletes_article((article_edit(("Nouveau.",)),))
    assert not deletes_article((edit(0, 3, ()),))


def chars(line, start, end, new="x", article="5"):
    return Splice.on_chars(article, line, start, end, new)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        # deux plages de caractères du même alinéa
        (chars(0, 2, 5), chars(0, 8, 9), False),  # disjointes
        (chars(0, 2, 5), chars(0, 5, 9), True),  # contiguës : les espaces de jonction en dépendent
        (chars(0, 2, 5), chars(0, 4, 9), True),  # recouvrement
        (chars(0, 3, 3), chars(0, 3, 3), True),  # même point d'insertion
        (chars(0, 2, 5), chars(1, 2, 5), False),  # alinéas différents
        # caractères contre alinéas
        (chars(1, 2, 5), edit(1, 2, ("y",)), True),  # l'alinéa est remplacé
        (chars(1, 2, 5), edit(0, 3, ()), True),  # l'alinéa est supprimé dans une plage
        (chars(1, 2, 5), edit(2, 3, ("y",)), False),  # un autre alinéa
        (chars(1, 2, 5), edit(1, 1, ("y",)), False),  # insertion avant l'alinéa
        (chars(1, 2, 5), edit(2, 2, ("y",)), False),  # insertion après l'alinéa
        (chars(1, 2, 5), article_edit(("y",)), True),
        # articles différents
        (chars(0, 2, 5, article="6"), article_edit(()), False),
    ],
)
def test_conflicts_on_characters(a, b, expected):
    assert conflicts(a, b) is expected
    assert conflicts(b, a) is expected


def test_apply_composes_characters_and_lines_in_parallel():
    lines = ("un chat noir", "deux chiens", "trois")
    patch = (
        chars(0, 3, 7, "rat"),  # « chat » → « rat »
        chars(0, 8, 12, "blanc"),  # « noir » → « blanc »
        chars(1, 0, 4, "2"),  # « deux » → « 2 »
        edit(2, 3, ()),  # supprime le troisième alinéa
        edit(0, 0, ("zéro",)),  # insère avant le premier
    )
    assert apply(lines, patch) == ("zéro", "un rat blanc", "2 chiens")


def test_apply_without_splice_keeps_the_lines():
    assert apply(("a", "b"), ()) == ("a", "b")


def test_apply_article_replacement_ignores_the_old_lines():
    assert apply(("a", "b"), (article_edit(("c",)),)) == ("c",)
    assert apply(("a", "b"), (article_edit(()),)) == ()
