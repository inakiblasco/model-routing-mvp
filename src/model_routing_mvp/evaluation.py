from __future__ import annotations

import re

from .domain import EvaluationResult, EvaluatorSpec


def evaluate(response: str, evaluator: EvaluatorSpec | None) -> EvaluationResult:
    if evaluator is None:
        return EvaluationResult(True, 1.0, "no evaluator configured")

    kind = str(evaluator.get("type", "")).lower()
    expected = str(evaluator.get("value", ""))

    if kind == "exact":
        passed = response.strip() == expected.strip()
    elif kind == "contains":
        passed = expected.lower() in response.lower()
    elif kind == "regex":
        passed = re.search(expected, response, flags=re.IGNORECASE) is not None
    else:
        return EvaluationResult(False, 0.0, f"unknown evaluator type: {kind}")

    return EvaluationResult(passed, 1.0 if passed else 0.0, kind)

