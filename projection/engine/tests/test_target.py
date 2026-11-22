import pytest

from engine.domain.refusal import Reason, Refusal
from engine.domain.target import Alineas, Anaphor, WholeArticle, resolve


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (Alineas((1,)), (0,)),
        (Alineas((3,)), (2,)),
        (Alineas((-1,)), (2,)),
        (Alineas((-2,)), (1,)),
        (Alineas((-3,)), (0,)),
        (Alineas((3, 1, 3)), (0, 2)),
        (Alineas((1, 2, 3)), (0, 1, 2)),
        (WholeArticle(), (0, 1, 2)),
        (WholeArticle("3"), (0, 1, 2)),
    ],
)
def test_resolve(target, expected):
    assert resolve(target, "3", 3) == expected


@pytest.mark.parametrize(
    ("target", "reason"),
    [
        (Alineas((0,)), Reason.TARGET_NOT_FOUND),
        (Alineas((4,)), Reason.TARGET_NOT_FOUND),
        (Alineas((-4,)), Reason.TARGET_NOT_FOUND),
        (Alineas((1, 4)), Reason.TARGET_NOT_FOUND),
        (WholeArticle("4"), Reason.UNRESOLVED_ARTICLE),
        (Anaphor(), Reason.OUT_OF_SCOPE),
    ],
)
def test_resolve_refuses(target, reason):
    with pytest.raises(Refusal) as refusal:
        resolve(target, "3", 3)
    assert refusal.value.reason is reason
