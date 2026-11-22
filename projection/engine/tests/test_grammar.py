from engine.reading import grammar
from engine.reading.grammar import GRAMMAR_VERSION, _version, parser


def test_grammar_version():
    assert len(GRAMMAR_VERSION) == 12
    int(GRAMMAR_VERSION, 16)
    assert GRAMMAR_VERSION == _version(grammar._grammar())
    assert _version(grammar._grammar() + " ") != GRAMMAR_VERSION


def test_parser_builds_both_entry_points():
    assert parser() is parser()
    assert parser().parse("Supprimer l'alinéa 2.", start="en_ligne") is not None
