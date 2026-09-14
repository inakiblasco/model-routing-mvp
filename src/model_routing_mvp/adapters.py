from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .domain import GenerationResult, TokenUsage


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _cost(
    usage: TokenUsage, input_cost_per_1k: float, output_cost_per_1k: float
) -> float:
    return (
        usage.input_tokens / 1000 * input_cost_per_1k
        + usage.output_tokens / 1000 * output_cost_per_1k
    )


def _infer_category(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in ("python", "function", "code", "bug")):
        return "coding"
    if any(word in text for word in ("reason", "logic", "conclude", "therefore")):
        return "reasoning"
    return "simple"


def _synthetic_answer(prompt: str) -> str:
    text = prompt.lower()
    if "2 + 2" in text or "2+2" in text:
        return "4"
    if "capital of france" in text:
        return "Paris"
    if "function named add" in text:
        return "def add(a: int, b: int) -> int:\n    return a + b"
    if "function named reverse_text" in text:
        return "def reverse_text(value: str) -> str:\n    return value[::-1]"
    if "alice has 3 apples" in text:
        return "Alice has 5 apples now."
    if "bloops" in text and "sally" in text:
        return "Sally is a razz."
    return "Synthetic answer unavailable for this prompt."


@dataclass(frozen=True)
class SyntheticModelAdapter:
    _model_name: str
    _provider: str
    capabilities: frozenset[str]
    latency_ms: int
    input_cost_per_1k: float
    output_cost_per_1k: float

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return self._provider

    def generate(self, prompt: str) -> GenerationResult:
        category = _infer_category(prompt)
        if category in self.capabilities:
            response = _synthetic_answer(prompt)
        else:
            response = "I am not confident enough to answer this task correctly."

        usage = TokenUsage(
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(response),
        )
        return GenerationResult(
            response=response,
            latency_s=self.latency_ms / 1000,
            token_usage=usage,
            estimated_cost_usd=_cost(
                usage, self.input_cost_per_1k, self.output_cost_per_1k
            ),
        )


@dataclass(frozen=True)
class OpenAICompatibleHTTPAdapter:
    """Small stdlib adapter for OpenAI-compatible chat completion endpoints."""

    _model_name: str
    _provider: str
    endpoint: str
    api_key_env: str | None
    input_cost_per_1k: float
    output_cost_per_1k: float
    timeout_s: float = 30

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return self._provider

    def generate(self, prompt: str) -> GenerationResult:
        if not self.endpoint:
            raise RuntimeError(f"Endpoint is not configured for {self.model_name}")

        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            api_key = os.environ.get(self.api_key_env)
            if not api_key:
                raise RuntimeError(
                    f"Missing API credential environment variable: {self.api_key_env}"
                )
            headers["Authorization"] = f"Bearer {api_key}"

        body = json.dumps(
            {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint, data=body, headers=headers, method="POST"
        )

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Model request failed for {self.model_name}") from exc

        latency_s = time.perf_counter() - start
        text = _extract_text(payload)
        usage = _extract_usage(payload, prompt, text)
        return GenerationResult(
            response=text,
            latency_s=latency_s,
            token_usage=usage,
            estimated_cost_usd=_cost(
                usage, self.input_cost_per_1k, self.output_cost_per_1k
            ),
        )


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    first = choices[0]
    message = first.get("message") or {}
    return str(message.get("content") or first.get("text") or "")


def _extract_usage(payload: dict[str, Any], prompt: str, response: str) -> TokenUsage:
    usage = payload.get("usage") or {}
    input_tokens = int(
        usage.get("prompt_tokens")
        or usage.get("input_tokens")
        or estimate_tokens(prompt)
    )
    output_tokens = int(
        usage.get("completion_tokens")
        or usage.get("output_tokens")
        or estimate_tokens(response)
    )
    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)

