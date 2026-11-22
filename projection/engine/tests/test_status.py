"""Tests du statut : dérivé de la raison de refus, ou imposé par la consolidation."""

import pytest

from engine.domain.refusal import Reason
from engine.domain.status import STATUS_OF_REASON, Status, status_of
from engine.domain.trace import Projection, Result


def projection(reason=None, result=None, **kwargs):
    return Projection("CE1", "3", result, reason, "", (), "v", **kwargs)


RESULT = Result("3", ("a",))


def test_every_reason_has_a_status():
    assert set(STATUS_OF_REASON) == set(Reason)


@pytest.mark.parametrize(
    ("reason", "result", "expected"),
    [
        pytest.param(None, RESULT, Status.APPLIED, id="applied"),
        pytest.param(Reason.AMBIGUOUS, None, Status.AMBIGUOUS, id="ambiguous"),
        pytest.param(Reason.QUOTE_MULTIPLE, None, Status.AMBIGUOUS, id="quote_multiple"),
        pytest.param(Reason.TARGET_NOT_FOUND, None, Status.PENDING, id="target_not_found"),
        pytest.param(Reason.TARGET_GONE, None, Status.PENDING, id="target_gone"),
        pytest.param(Reason.QUOTE_MISSING, None, Status.PENDING, id="quote_missing"),
        pytest.param(Reason.UNRESOLVED_ARTICLE, None, Status.PENDING, id="unresolved_article"),
        pytest.param(Reason.INCONSISTENT_BLOCK, None, Status.PENDING, id="inconsistent_block"),
        pytest.param(Reason.CONFLICT, None, Status.PENDING, id="conflict"),
        pytest.param(Reason.OUT_OF_SCOPE, None, Status.NOT_PARSED, id="out_of_scope"),
    ],
)
def test_status_of(reason, result, expected):
    assert status_of(reason, result) is expected


def test_status_follows_the_projection():
    assert projection(result=RESULT).status is Status.APPLIED
    assert projection(Reason.QUOTE_MISSING).status is Status.PENDING


def test_forced_status_is_honoured():
    forced = projection(result=RESULT, forced=Status.IDENTICAL)
    assert forced.status is Status.IDENTICAL and forced.applied


def test_forced_does_not_change_reason_or_result():
    plain = projection(Reason.OUT_OF_SCOPE)
    forced = projection(Reason.OUT_OF_SCOPE, forced=Status.SUB_AMENDMENT)
    assert (forced.reason, forced.result) == (plain.reason, plain.result)


def test_projection_without_forced_equals_as_before():
    assert projection(Reason.CONFLICT) == projection(Reason.CONFLICT, forced=None)
    assert projection(Reason.CONFLICT) != projection(Reason.CONFLICT, forced=Status.IDENTICAL)
