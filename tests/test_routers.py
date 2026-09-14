from __future__ import annotations

import pytest

from model_routing_mvp.domain import Task
from model_routing_mvp.routers import AlwaysRouter, RuleBasedRouter


_MODELS = {"fast": object(), "coding": object(), "strong": object()}


def test_always_router_selects_configured_model() -> None:
    router = AlwaysRouter("always_fast", "fast")
    task = Task("t1", "prompt", "reasoning")

    decision = router.route(task, _MODELS)  # type: ignore[arg-type]

    assert decision.strategy == "always_fast"
    assert decision.model_key == "fast"
    assert "always selects fast" in decision.reason


def test_rule_based_router_selects_category_route() -> None:
    router = RuleBasedRouter(
        "rule_based_router",
        routes={"simple": "fast", "coding": "coding", "reasoning": "strong"},
        fallback_model_key="strong",
    )

    decision = router.route(Task("t1", "prompt", "coding"), _MODELS)  # type: ignore[arg-type]

    assert decision.model_key == "coding"
    assert decision.reason == "category=coding -> coding"


def test_rule_based_router_uses_fallback_for_unknown_category() -> None:
    router = RuleBasedRouter("rule_based_router", routes={}, fallback_model_key="strong")

    decision = router.route(Task("t1", "prompt", "unknown"), _MODELS)  # type: ignore[arg-type]

    assert decision.model_key == "strong"


def test_router_fails_fast_when_selected_model_is_missing() -> None:
    router = AlwaysRouter("always_missing", "missing")

    with pytest.raises(KeyError, match="missing"):
        router.route(Task("t1", "prompt", "simple"), {})