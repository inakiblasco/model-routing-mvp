from __future__ import annotations

from dataclasses import dataclass

from .domain import ModelAdapter, RouteDecision, Task


@dataclass(frozen=True)
class AlwaysRouter:
    name: str
    model_key: str

    def route(
        self, task: Task, models: dict[str, ModelAdapter]
    ) -> RouteDecision:
        _require_model(self.model_key, models)
        return RouteDecision(
            strategy=self.name,
            model_key=self.model_key,
            reason=f"baseline always selects {self.model_key}",
        )


@dataclass(frozen=True)
class RuleBasedRouter:
    name: str
    routes: dict[str, str]
    fallback_model_key: str

    def route(
        self, task: Task, models: dict[str, ModelAdapter]
    ) -> RouteDecision:
        model_key = self.routes.get(task.expected_category, self.fallback_model_key)
        _require_model(model_key, models)
        return RouteDecision(
            strategy=self.name,
            model_key=model_key,
            reason=f"category={task.expected_category} -> {model_key}",
        )


def _require_model(model_key: str, models: dict[str, ModelAdapter]) -> None:
    if model_key not in models:
        raise KeyError(f"Router selected missing model: {model_key}")

