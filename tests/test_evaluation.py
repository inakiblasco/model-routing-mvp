from __future__ import annotations

import pytest

from model_routing_mvp.evaluation import evaluate


@pytest.mark.parametrize(
    ("response", "evaluator", "passed"),
    [
        (" 4 ", {"type": "exact", "value": "4"}, True),
        ("Paris, France", {"type": "contains", "value": "paris"}, True),
        ("Answer: 42", {"type": "regex", "value": r"answer:\s*\d+"}, True),
        ("wrong", {"type": "exact", "value": "right"}, False),
        ("anything", {"type": "unknown", "value": "anything"}, False),
    ],
)
def test_evaluate_supported_and_unknown_evaluators(
    response: str, evaluator: dict[str, str], passed: bool
) -> None:
    result = evaluate(response, evaluator)

    assert result.passed is passed
    assert result.score == (1.0 if passed else 0.0)


def test_missing_evaluator_is_marked_passed_but_explicit() -> None:
    result = evaluate("unscored response", None)

    assert result.passed is True
    assert result.score == 1.0
    assert result.details == "no evaluator configured"