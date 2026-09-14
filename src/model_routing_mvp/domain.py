from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


EvaluatorSpec = dict[str, Any]


@dataclass(frozen=True)
class Task:
    task_id: str
    prompt: str
    expected_category: str
    evaluator: EvaluatorSpec | None = None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class GenerationResult:
    response: str
    latency_s: float
    token_usage: TokenUsage
    estimated_cost_usd: float


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    score: float
    details: str


@dataclass(frozen=True)
class RouteDecision:
    strategy: str
    model_key: str
    reason: str


class ModelAdapter(Protocol):
    @property
    def model_name(self) -> str:
        ...

    @property
    def provider(self) -> str:
        ...

    def generate(self, prompt: str) -> GenerationResult:
        ...


class Router(Protocol):
    @property
    def name(self) -> str:
        ...

    def route(
        self, task: Task, models: dict[str, ModelAdapter]
    ) -> RouteDecision:
        ...

