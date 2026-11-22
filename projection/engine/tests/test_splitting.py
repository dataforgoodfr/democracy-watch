import pytest

from engine.domain.refusal import Reason, Refusal
from engine.reading.splitting import block_citations, split_units


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (("A.", "B."), (("A.", "B."),)),
        (("I. – A.",), (("A.",),)),
        (("I. – A.", "II. – B."), (("A.",), ("B.",))),
        (("I. – A.", "«x»", "II. — B.", "III. - C."), (("A.", "«x»"), ("B.",), ("C.",))),
        (("I. –", "A.", "II. – B."), (("A.",), ("B.",))),
        (("I. – A.", "II. –"), (("A.",), ())),
        (
            ("I. – A.", "II. – B.", "III. – C.", "IV. – D."),
            (("A.",), ("B.",), ("C.",), ("D.",)),
        ),
        (("«I. – A.", "II. – B."), (("«I. – A.", "II. – B."),)),
        (("A.", "II. – B."), (("A.", "II. – B."),)),
        (("I. – A.", "«II. – B.»"), (("A.", "«II. – B.»"),)),
    ],
)
def test_split_units(lines, expected):
    assert split_units(lines) == expected


@pytest.mark.parametrize(
    ("lines", "reason"),
    [
        ((), Reason.OUT_OF_SCOPE),
        (("II. – A.",), Reason.AMBIGUOUS),
        (("I. – A.", "III. – B."), Reason.AMBIGUOUS),
        (("I. – A.", "II. – B.", "II. – C."), Reason.AMBIGUOUS),
        (("I. – A.", "I. – B."), Reason.AMBIGUOUS),
    ],
)
def test_split_units_refusals(lines, reason):
    with pytest.raises(Refusal) as error:
        split_units(lines)
    assert error.value.reason == reason


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (("«a»",), ("a",)),
        (("« a »",), ("a",)),
        (("«a».",), ("a",)),
        (("«a»;",), ("a",)),
        (("«a» .",), ("a",)),
        (("«a", "«b»"), ("a", "b")),
        (("«a", "« b", "«c»."), ("a", "b", "c")),
        ((" «a ", " « b» "), ("a", "b")),
        (("«a, «b» c»",), ("a, «b» c",)),
    ],
)
def test_block_citations(lines, expected):
    assert block_citations(lines) == expected


@pytest.mark.parametrize(
    "lines",
    [
        (),
        ("a»",),
        ("«a",),
        ("«a»", "«b»"),
        ("«a", "b»"),
        ("«a»", "«b»", "«c»"),
        ("«a;", "b»"),
        ("«a»", "b»"),
        ("«»",),
        ("« »",),
        ("«a", "«»"),
    ],
)
def test_block_citations_refusals(lines):
    with pytest.raises(Refusal) as error:
        block_citations(lines)
    assert error.value.reason == Reason.INCONSISTENT_BLOCK
