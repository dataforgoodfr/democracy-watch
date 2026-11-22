import pytest

from engine.domain.documents import Article, Text
from engine.domain.refusal import Reason, Refusal


def refusal_of(text, number):
    with pytest.raises(Refusal) as refusal:
        text.find(number)
    assert refusal.value.reason is Reason.UNRESOLVED_ARTICLE


def test_find_returns_the_unique_article():
    article = Article("3", ("a",))
    assert Text("T", (Article("2", ("b",)), article)).find("3") is article


def test_find_refuses_absent_and_duplicated_articles():
    refusal_of(Text("T", (Article("2", ("b",)),)), "3")
    refusal_of(Text("T", (Article("3", ("a",)), Article("3", ("b",)))), "3")


@pytest.mark.parametrize("flag", ["unchanged", "from_range"])
def test_find_refuses_an_article_without_known_text(flag):
    refusal_of(Text("T", (Article("3", (), **{flag: True}),)), "3")
