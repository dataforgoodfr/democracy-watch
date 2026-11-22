import pytest

from engine.domain.normalization import article_number, normalize


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a b", "a b"),
        ("a b", "a b"),
        ("a‑b", "a-b"),
        ("l’article", "l'article"),
        ("« a »", "«a»"),
        ("« a »", "«a»"),
        ("«  a  b  »", "«a  b»"),
        ("  a  ", "  a  "),
        ("", ""),
    ],
)
def test_normalize(text, expected):
    assert normalize(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1er", "PREMIER"),
        ("1ER", "PREMIER"),
        ("1 er", "PREMIER"),
        ("premier", "PREMIER"),
        (" 3  bis ", "3 BIS"),
        ("12 ter a", "12 TER A"),
        ("unique", "UNIQUE"),
        ("11", "11"),
    ],
)
def test_article_number(text, expected):
    assert article_number(text) == expected
