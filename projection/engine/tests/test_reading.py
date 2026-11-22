import pytest

from engine.actions import (
    DeleteEnd,
    DeleteNode,
    DeleteWords,
    InsertEdge,
    InsertNode,
    InsertWords,
    Rewrite,
    RewriteEnd,
    Substitute,
)
from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, WholeArticle
from engine.domain.writing import Anchor
from engine.reading import read
from engine.reading.inline import _Action
from engine.reading.ordinals import CARDINALS, ORDINALS
from engine.reading.reader import ToOperations

AL2 = Alineas((2,))


def single(*lines):
    (instruction,) = read(lines)
    return instruction


def sequence(*sentences):
    """Dispositif en unités numérotées « I. – », « II. – »…."""
    romans = ("I", "II", "III")
    return read(tuple(f"{roman}. – {text}" for roman, text in zip(romans, sentences, strict=False)))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "À l'alinéa 2, substituer au mot : «second», le mot : «dernier».",
            Substitute(AL2, Anchor("second"), "dernier"),
        ),
        (
            "À l’alinéa 2, remplacer les mots : «a b» par les mots : «c».",
            Substitute(AL2, Anchor("a b"), "c"),
        ),
        (
            "À l'alinéa 2, substituer à la seconde occurrence du mot : «a», le mot : «b».",
            Substitute(AL2, Anchor("a", 2), "b"),
        ),
        (
            "Au dernier alinéa, substituer à la référence : «L. 1», la référence : «L. 2».",
            Substitute(Alineas((-1,)), Anchor("L. 1"), "L. 2"),
        ),
        ("À l'alinéa 2, supprimer les mots : «a».", DeleteWords(AL2, Anchor("a"))),
        (
            "Au deuxième alinéa, supprimer la dernière occurrence du mot : «a».",
            DeleteWords(AL2, Anchor("a", -1)),
        ),
        (
            "À l'alinéa 2, après le mot : «a», insérer les mots : «b».",
            InsertWords(AL2, Anchor("a"), "b", True),
        ),
        (
            "À l'alinéa 2, avant les mots : «a», insérer le mot : «b».",
            InsertWords(AL2, Anchor("a"), "b", False),
        ),
        (
            "À l'alinéa 2, après la première occurrence du mot : «a», insérer le mot : «b».",
            InsertWords(AL2, Anchor("a", 1), "b", True),
        ),
        (
            "Aux alinéas 2 et 4, après le mot : «a», ajouter les mots : «b».",
            InsertWords(Alineas((2, 4)), Anchor("a"), "b", True),
        ),
        (
            "À la fin de l'alinéa 2, insérer les mots : «b».",
            InsertEdge(AL2, "b", False),
        ),
        (
            "Au début de l'alinéa 2, insérer les mots : «b».",
            InsertEdge(AL2, "b", True),
        ),
        (
            "Compléter l'alinéa 2 par les mots : «b».",
            InsertEdge(AL2, "b", False),
        ),
        (
            "Compléter cet article par la référence : «b».",
            InsertEdge(WholeArticle(), "b", False),
        ),
        ("Supprimer l'alinéa 2.", DeleteNode(AL2)),
        ("Supprimer les alinéas 2 à 4.", DeleteNode(Alineas((2, 3, 4)))),
        ("Supprimer les alinéas 2, 4 et 6.", DeleteNode(Alineas((2, 4, 6)))),
        ("Supprimer cet article.", DeleteNode(WholeArticle())),
        ("Supprimer l'article 3.", DeleteNode(WholeArticle("3"))),
        # rÃ©diger ainsi, en ligne
        ("Rédiger ainsi l'alinéa 2 : «x y».", Rewrite(AL2, ("x y",))),
        ("Rédiger ainsi cet article : «x».", Rewrite(WholeArticle(), ("x",))),
        (
            "À l'alinéa 15, après les mots : «a», rédiger ainsi la fin de l'alinéa : «b».",
            RewriteEnd(Alineas((15,)), Anchor("a"), "b"),
        ),
        (
            "Après le mot : «a», rédiger ainsi la fin de l'alinéa 3 : «b».",
            RewriteEnd(Alineas((3,)), Anchor("a"), "b"),
        ),
        (
            "À l'alinéa 3, après le mot : «a», supprimer la fin de l'alinéa.",
            DeleteEnd(Alineas((3,)), Anchor("a")),
        ),
        (
            "Après le mot : «a», supprimer la fin de l'alinéa 3.",
            DeleteEnd(Alineas((3,)), Anchor("a")),
        ),
    ],
)
def test_en_ligne(text, expected):
    instruction = single(text)
    assert instruction.operation == expected
    assert instruction.reason is None
    assert instruction.text == text


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("Supprimer l'article 1er.", WholeArticle("PREMIER")),
        ("Supprimer l'article premier.", WholeArticle("PREMIER")),
        ("Supprimer l'article unique.", WholeArticle("UNIQUE")),
        ("Supprimer l'article 3 bis.", WholeArticle("3 BIS")),
        ("Supprimer l'article 12  ter A.", WholeArticle("12 TER A")),
        ("Supprimer le premier alinéa.", Alineas((1,))),
        ("Supprimer le second alinéa.", Alineas((2,))),
        ("Supprimer le dernier alinéa.", Alineas((-1,))),
        ("Supprimer l'avant-dernier alinéa.", Alineas((-2,))),
        ("Supprimer l’avant-dernier alinéa.", Alineas((-2,))),
        ("Supprimer la seconde alinéa.", Alineas((2,))),
        ("Supprimer le Vingtième alinéa.", Alineas((20,))),
        ("Supprimer les alinéas 3 à 3.", Alineas((3,))),
    ],
)
def test_targets(text, target):
    assert single(text).operation == DeleteNode(target)


@pytest.mark.parametrize(
    ("text", "operation"),
    [
        (
            "À l'alinéa 2, supprimer les mots : «a».",
            DeleteWords(AL2, Anchor("a")),
        ),
        (
            "À l'alinéa 2, supprimer l'alinéa 2.",
            DeleteNode(AL2),
        ),
        (
            "À l'alinéa 15, après les mots : «a», rédiger ainsi la fin de l'alinéa : «b».",
            RewriteEnd(Alineas((15,)), Anchor("a"), "b"),
        ),
        (
            "À l'alinéa 15, après les mots : «a», rédiger ainsi la fin de l'alinéa 15 : «b».",
            RewriteEnd(Alineas((15,)), Anchor("a"), "b"),
        ),
        (
            "À l'alinéa 3, compléter l'alinéa 3 par les mots : «b».",
            InsertEdge(Alineas((3,)), "b", False),
        ),
    ],
)
def test_prefix_and_action_target_are_merged(text, operation):
    assert single(text).operation == operation


def test_prefix_and_action_targets_differ():
    instruction = single("À l'alinéa 2, supprimer l'alinéa 3.")
    assert instruction.reason is Reason.AMBIGUOUS
    assert instruction.detail == "deux cibles"


@pytest.mark.parametrize(
    "text",
    [
        "À la fin de l'alinéa 1, supprimer le mot : «Le».",
        "Au début de l'alinéa 1, supprimer les mots : «Le».",
        "À la fin de l'alinéa 1, substituer au mot : «a», le mot : «b».",
        "À la fin de l'alinéa 1, compléter l'alinéa 1 par les mots : «b».",
        "À la fin de l'alinéa 1, supprimer l'alinéa 1.",
        "À la fin de l'alinéa 1, après le mot : «a», supprimer la fin de l'alinéa.",
    ],
)
def test_edge_prefix_only_with_insertion(text):
    assert single(text).reason is Reason.OUT_OF_SCOPE


def test_anaphor_with_concrete_target_in_same_sentence():
    assert single("À l'alinéa 2, supprimer cet alinéa.").operation == DeleteNode(AL2)
    expected = RewriteEnd(AL2, Anchor("a"), "b")
    text = "À l'alinéa 2, après le mot : «a», rédiger ainsi la fin de cet alinéa : «b»."
    assert single(text).operation == expected


@pytest.mark.parametrize("text", ["Supprimer cet alinéa.", "À cet alinéa, supprimer cet alinéa."])
def test_lone_anaphor_without_antecedent(text):
    instruction = single(text)
    assert instruction.reason is Reason.TARGET_NOT_FOUND
    assert "antécédent absent" in instruction.detail


def test_anaphor_resolved_by_previous_instruction():
    instructions = sequence("À l'alinéa 2, supprimer les mots : «a».", "Supprimer le même alinéa.")
    assert [i.operation for i in instructions] == [
        DeleteWords(AL2, Anchor("a")),
        DeleteNode(AL2),
    ]


def test_meme_alinea_with_number_is_ambiguous():
    instructions = sequence(
        "À l'alinéa 2, supprimer les mots : «a».",
        "À la fin du même alinéa 4, insérer les mots : «b».",
    )
    assert instructions[1].reason is Reason.AMBIGUOUS
    assert "numéro et renvoi" in instructions[1].detail


def test_anaphor_after_refused_instruction():
    instructions = sequence("Supprimer le titre.", "Supprimer cet alinéa.")
    assert instructions[1].reason is Reason.TARGET_NOT_FOUND


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Procéder à la même substitution à l'alinéa 5.",
            Substitute(Alineas((5,)), Anchor("a"), "b"),
        ),
        (
            "À l'alinéa 5, procéder à la même substitution.",
            Substitute(Alineas((5,)), Anchor("a"), "b"),
        ),
        (
            "Procéder à la même substitution aux alinéas 5 et 6.",
            Substitute(Alineas((5, 6)), Anchor("a"), "b"),
        ),
    ],
)
def test_renvoi_replays_previous_operation(text, expected):
    instructions = sequence("À l'alinéa 2, substituer au mot : «a», le mot : «b».", text)
    assert instructions[1].operation == expected


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("Procéder à la même substitution.", Reason.TARGET_NOT_FOUND),
        ("Procéder à la même substitution à cet alinéa.", Reason.OUT_OF_SCOPE),
        ("Procéder à la même substitution à cet article.", Reason.OUT_OF_SCOPE),
        ("Procéder à la même suppression à l'alinéa 5.", Reason.AMBIGUOUS),
        ("Procéder à la même substitution à la fin de l'alinéa 5.", Reason.OUT_OF_SCOPE),
        ("Procéder à la même substitution au début de l'alinéa 5.", Reason.OUT_OF_SCOPE),
        ("À l'alinéa 4, procéder à la même substitution à l'alinéa 5.", Reason.AMBIGUOUS),
    ],
)
def test_renvoi_refusals(text, reason):
    instructions = sequence("À l'alinéa 2, substituer au mot : «a», le mot : «b».", text)
    assert instructions[1].reason is reason


def test_renvoi_alone_has_no_antecedent():
    assert single("Procéder à la même substitution à l'alinéa 5.").reason is Reason.TARGET_NOT_FOUND


@pytest.mark.parametrize(("word", "rank"), list(ORDINALS.items()))
def test_every_ordinal(word, rank):
    assert single(f"Supprimer le {word} alinéa.").operation == DeleteNode(Alineas((rank,)))
    expected = DeleteWords(AL2, Anchor("a", rank))
    assert single(f"À l'alinéa 2, supprimer la {word} occurrence du mot : «a».").operation == (
        expected
    )


@pytest.mark.parametrize(("word", "count"), list(CARDINALS.items()))
def test_every_cardinal(word, count):
    def lines(number):
        body = ["«x"] * (number - 1) + ["«x»"]
        return (f"Compléter cet article par les {word} alinéas suivants :", *body)

    assert single(*lines(count)).operation == InsertNode(WholeArticle(), ("x",) * count, True)
    for wrong in (count - 1, count + 1):
        assert single(*lines(wrong)).reason is Reason.INCONSISTENT_BLOCK


def test_missing_target():
    instruction = single("Après le mot : «a», supprimer la fin de l'alinéa.")
    assert instruction.reason is Reason.TARGET_NOT_FOUND
    assert "antécédent absent" in instruction.detail
    instruction = single("Supprimer les mots : «a».")
    assert instruction.reason is Reason.TARGET_NOT_FOUND


@pytest.mark.parametrize(
    "text",
    [
        "Insérer les mots : «b».",
        "À l'alinéa 2, insérer les mots : «b».",
        "À l'alinéa 2, ajouter la référence : «b».",
    ],
)
def test_insertion_needs_start_or_end_prefix(text):
    assert single(text).reason is Reason.OUT_OF_SCOPE


@pytest.mark.parametrize(
    "text",
    [
        "À l'alinéa 2, avant le mot : «a», rédiger ainsi la fin de l'alinéa : «b».",
        "À l'alinéa 2, avant le mot : «a», supprimer la fin de l'alinéa.",
    ],
)
def test_end_of_alinea_only_after_anchor(text):
    assert single(text).reason is Reason.OUT_OF_SCOPE


@pytest.mark.parametrize(
    "text",
    [
        "Bonjour tout le monde.",
        "À l'alinéa 2, supprimer les mots.",
        "À l'alinéa 2, substituer au mot : «a», le mot : «b», le mot : «c».",
        "",
    ],
)
def test_outside_grammar(text):
    instruction = single(text)
    assert instruction.operation is None
    assert instruction.reason is Reason.OUT_OF_SCOPE
    assert instruction.detail == "hors grammaire"


@pytest.mark.parametrize(
    "text",
    [
        "À la seconde phrase de l'alinéa 2, supprimer les mots : «a».",
        "La première phrase de l'alinéa 2, supprimer les mots : «a».",
        "À la même phrase, supprimer les mots : «a».",
        "À ladite phrase de l'alinéa 2, supprimer les mots : «a».",
        "Supprimer le titre.",
        "Supprimer cet amendement.",
        "À l'alinéa 2, insérer la phrase suivante : «a.»",
        "À l'alinéa 2, compléter l'alinéa par les deux phrases suivantes : «a. b.»",
        "Compléter l'alinéa 2 par la phrase suivante : «b.»",
        "Rédiger ainsi la première phrase de l'alinéa 2 : «x».",
        "Supprimer la deuxième phrase de l'alinéa 2.",
    ],
)
def test_out_of_scope_rules(text):
    instruction = single(text)
    assert instruction.operation is None
    assert instruction.reason is Reason.OUT_OF_SCOPE


@pytest.mark.parametrize(
    "text",
    [
        "À l'alinéa 2, supprimer les mots : «».",
        "À l'alinéa 2, substituer au mot : «a», le mot : «».",
        "Rédiger ainsi l'alinéa 2 : «».",
    ],
)
def test_empty_quotation(text):
    instruction = single(text)
    assert instruction.reason is Reason.OUT_OF_SCOPE
    assert instruction.detail == "citation vide"


def test_instruction_pieces_in_separate_lines():
    lines = ("À l'alinéa 2, substituer au mot :", "«a»,", "le mot :", "«b».")
    instruction = single(*lines)
    assert instruction.operation == Substitute(AL2, Anchor("a"), "b")
    assert instruction.text == " ".join(lines)


def test_quotation_over_several_lines_is_refused():
    instruction = single("Rédiger ainsi l'alinéa 2 : «a", "b».")
    assert instruction.reason is Reason.INCONSISTENT_BLOCK
    assert instruction.detail == "citation sur plusieurs lignes"


def test_inverted_range():
    instruction = single("Supprimer les alinéas 5 à 3.")
    assert instruction.reason is Reason.TARGET_NOT_FOUND


# ---- blocs


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (
            ("Rédiger ainsi cet article :", "«A", "«B»."),
            Rewrite(WholeArticle(), ("A", "B")),
        ),
        (
            ("Rédiger ainsi l'alinéa 3 :", "«A»."),
            Rewrite(Alineas((3,)), ("A",)),
        ),
        (
            ("Substituer à l'alinéa 3 les deux alinéas suivants :", "«A", "«B»."),
            Rewrite(Alineas((3,)), ("A", "B")),
        ),
        (
            ("Substituer aux alinéas 3 à 5 l'alinéa suivant :", "«A»."),
            Rewrite(Alineas((3, 4, 5)), ("A",)),
        ),
        (
            ("Après l'alinéa 3, insérer l'alinéa suivant :", "«A»."),
            InsertNode(Alineas((3,)), ("A",), True),
        ),
        (
            ("Avant l'alinéa 3, insérer un alinéa ainsi rédigé :", "«A»."),
            InsertNode(Alineas((3,)), ("A",), False),
        ),
        (
            (
                "Après l'alinéa 3, insérer les six alinéas suivants :",
                "«A",
                "«B",
                "«C",
                "«D",
                "«E",
                "«F».",
            ),
            InsertNode(Alineas((3,)), ("A", "B", "C", "D", "E", "F"), True),
        ),
        (
            ("Après le dernier alinéa, insérer les 2 alinéas suivants :", "«A", "«B»."),
            InsertNode(Alineas((-1,)), ("A", "B"), True),
        ),
        (
            ("Au début de cet article, insérer l'alinéa suivant :", "«A»."),
            InsertNode(WholeArticle(), ("A",), False),
        ),
        (
            ("Au début de l'article 3, insérer les deux alinéas suivants :", "«A", "«B»."),
            InsertNode(WholeArticle("3"), ("A", "B"), False),
        ),
        (
            ("Compléter cet article par l'alinéa suivant :", "«A»."),
            InsertNode(WholeArticle(), ("A",), True),
        ),
        (
            ("Compléter l'alinéa 2 par les mots :", "«B»."),
            InsertEdge(AL2, "B", False),
        ),
        (
            ("Compléter cet article par les alinéas suivants :", "«A", "«B»."),
            InsertNode(WholeArticle(), ("A", "B"), True),
        ),
    ],
)
def test_bloc(lines, expected):
    instruction = single(*lines)
    assert instruction.operation == expected
    assert instruction.text == " ".join(lines)


@pytest.mark.parametrize(
    ("lines", "reason"),
    [
        # nombre annoncé différent du nombre cité
        (
            ("Après l'alinéa 3, insérer les deux alinéas suivants :", "«A»."),
            Reason.INCONSISTENT_BLOCK,
        ),
        (("Après l'alinéa 3, insérer l'alinéa suivant :", "«A", "«B»."), Reason.INCONSISTENT_BLOCK),
        (
            ("Substituer à l'alinéa 3 les trois alinéas suivants :", "«A", "«B»."),
            Reason.INCONSISTENT_BLOCK,
        ),
        (
            ("Compléter cet article par les 3 alinéas suivants :", "«A", "«B»."),
            Reason.INCONSISTENT_BLOCK,
        ),
        # compléter par des mots : un seul alinéa
        (("Compléter l'alinéa 2 par les mots :", "«A", "«B»."), Reason.INCONSISTENT_BLOCK),
        # chapeau sans corps, ou corps mal formé
        (("Rédiger ainsi cet article :",), Reason.INCONSISTENT_BLOCK),
        (("Rédiger ainsi cet article :", "A»."), Reason.INCONSISTENT_BLOCK),
        (("Rédiger ainsi cet article :", "«A"), Reason.INCONSISTENT_BLOCK),
        (("Rédiger ainsi cet article :", "«A»", "«B»."), Reason.INCONSISTENT_BLOCK),
        # hors périmètre
        (("Après l'article 3, insérer l'article suivant :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Après les alinéas 3 et 4, insérer l'alinéa suivant :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Après cet alinéa, insérer l'alinéa suivant :", "«A»."), Reason.TARGET_NOT_FOUND),
        (("Au début de l'alinéa 3, insérer l'alinéa suivant :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Au début, insérer l'alinéa suivant :", "«A»."), Reason.TARGET_NOT_FOUND),
        (("Substituer à l'alinéa 3 la phrase suivante :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Substituer à l'alinéa 3 les deux phrases suivantes :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Rédiger ainsi le titre :", "«A»."), Reason.OUT_OF_SCOPE),
        (
            ("Rétablir le I de l'alinéa 3 dans la rédaction suivante :", "«A»."),
            Reason.OUT_OF_SCOPE,
        ),
        # rétablir n'écrase pas : refusé
        (("Rétablir l'alinéa 3 dans la rédaction suivante :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Rétablir l'article 3 dans la rédaction suivante :", "«A»."), Reason.OUT_OF_SCOPE),
        # alinéas ajoutés à un alinéa : ce n'est pas « compléter l'alinéa »
        (("Compléter l'alinéa 1 par un alinéa ainsi rédigé :", "«A»."), Reason.OUT_OF_SCOPE),
        (
            ("Compléter l'alinéa 2 par les deux alinéas suivants :", "«A", "«B»."),
            Reason.OUT_OF_SCOPE,
        ),
        (("Rédiger ainsi la seconde phrase :", "«A»."), Reason.OUT_OF_SCOPE),
        (("Un texte libre :", "«A»."), Reason.OUT_OF_SCOPE),
    ],
)
def test_bloc_refusals(lines, reason):
    instruction = single(*lines)
    assert instruction.operation is None
    assert instruction.reason is reason


def test_alineas_sans_nombre_only_in_last_unit():
    assert single("Compléter cet article par les alinéas suivants :", "«A", "«B».").operation == (
        InsertNode(WholeArticle(), ("A", "B"), True)
    )
    first, last = read(
        (
            "I. – Après l'alinéa 2, insérer les alinéas suivants :",
            "«A",
            "«B».",
            "II. – Compléter cet article par les alinéas suivants :",
            "«C",
            "«D».",
        )
    )
    assert first.reason is Reason.INCONSISTENT_BLOCK
    assert last.operation == InsertNode(WholeArticle(), ("C", "D"), True)


# ---- en ligne contre bloc, unités


@pytest.mark.parametrize(
    ("text", "position"),
    [
        ("Après l'avant-dernier alinéa, insérer l'alinéa suivant :", -2),
        ("Après le dernier alinéa, insérer l'alinéa suivant :", -1),
    ],
)
def test_block_after_relative_alinea(text, position):
    assert single(text, "«A».").operation == InsertNode(Alineas((position,)), ("A",), True)


def test_single_line_block_is_read_in_line():
    instruction = single("Rédiger ainsi l'alinéa 3 : «A».")
    assert instruction.operation == Rewrite(Alineas((3,)), ("A",))


def test_analyze_never_raises():
    assert read(())[0].reason is Reason.OUT_OF_SCOPE
    # marqueurs hors suite : une seule instruction refusée
    (instruction,) = read(("I. – Supprimer l'alinéa 2.", "III. – Supprimer l'alinéa 3."))
    assert instruction.reason is Reason.AMBIGUOUS
    assert instruction.text == "I. – Supprimer l'alinéa 2. III. – Supprimer l'alinéa 3."
    # unité vide
    assert read(("I. –", "II. – Supprimer l'alinéa 2."))[0].reason is Reason.OUT_OF_SCOPE


# ---- ambiguïté et grammaire


def test_ambiguous_alternatives():
    transformer = ToOperations((), True)
    same = _Action(DeleteNode, (), AL2)
    assert transformer._ambig([same, _Action(DeleteNode, (), AL2)]) is same
    assert transformer._ambig([DeleteNode(AL2), DeleteNode(AL2)]) == DeleteNode(AL2)
    for other in (_Action(DeleteNode, (), Alineas((3,))), _Action(Rewrite, ((),), AL2)):
        with pytest.raises(Refusal) as error:
            transformer._ambig([same, other])
        assert error.value.reason is Reason.AMBIGUOUS


def test_analyze_does_not_raise_on_ambiguity(monkeypatch):
    def ambiguous(self, alternatives):
        raise Refusal(Reason.AMBIGUOUS, "plusieurs analyses")

    monkeypatch.setattr(ToOperations, "en_ligne", ambiguous)
    instruction = single("Supprimer l'alinéa 2.")
    assert instruction.reason is Reason.AMBIGUOUS
    assert instruction.detail == "plusieurs analyses"
