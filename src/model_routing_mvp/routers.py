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


@dataclass(frozen=True)
class PolicyRouter:
    name: str
    fast_model_key: str
    standard_model_key: str
    strong_model_key: str

    def route(
        self, task: Task, models: dict[str, ModelAdapter]
    ) -> RouteDecision:
        task_type = (task.task_type or task.expected_category).lower()
        risk = task.risk.lower()
        sensitivity = task.sensitivity.lower()

        if risk == "high" or sensitivity in {"confidential", "restricted"}:
            model_key = self.strong_model_key
            reason = f"risk={risk}, sensitivity={sensitivity} -> strong"
        elif task.expected_category == "reasoning" or task_type in {
            "architecture",
            "legal",
            "security",
        }:
            model_key = self.strong_model_key
            reason = f"task_type={task_type}, category={task.expected_category} -> strong"
        elif task.expected_category == "coding" or task_type in {
            "coding",
            "debugging",
            "data_extraction",
            "research",
            "summarization",
        }:
            model_key = self.standard_model_key
            reason = f"task_type={task_type}, category={task.expected_category} -> standard"
        else:
            model_key = self.fast_model_key
            reason = f"task_type={task_type}, risk={risk} -> fast"

        _require_model(model_key, models)
        return RouteDecision(
            strategy=self.name,
            model_key=model_key,
            reason=reason,
        )


def _require_model(model_key: str, models: dict[str, ModelAdapter]) -> None:
    if model_key not in models:
        raise KeyError(f"Router selected missing model: {model_key}")
