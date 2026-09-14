from __future__ import annotations

import json
import urllib.error
from typing import Any

import pytest

from model_routing_mvp.adapters import (
    OpenAICompatibleHTTPAdapter,
    SyntheticModelAdapter,
    estimate_tokens,
)


def test_estimate_tokens_never_returns_zero() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("one two") == 2


def test_synthetic_model_respects_capabilities_and_costs() -> None:
    model = SyntheticModelAdapter(
        _model_name="fast-sim",
        _provider="local-synthetic",
        capabilities=frozenset({"simple"}),
        latency_ms=250,
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.002,
    )

    simple = model.generate("What is 2 + 2?")
    coding = model.generate("Write a Python function named add.")

    assert simple.response == "4"
    assert simple.latency_s == 0.25
    assert simple.estimated_cost_usd > 0
    assert "not confident" in coding.response


def test_http_adapter_requires_endpoint() -> None:
    adapter = OpenAICompatibleHTTPAdapter(
        _model_name="remote-model",
        _provider="remote",
        endpoint="",
        api_key_env=None,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
    )

    with pytest.raises(RuntimeError, match="Endpoint is not configured"):
        adapter.generate("hello")


def test_http_adapter_requires_configured_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_API_KEY", raising=False)
    adapter = OpenAICompatibleHTTPAdapter(
        _model_name="remote-model",
        _provider="remote",
        endpoint="https://example.invalid/v1/chat/completions",
        api_key_env="MISSING_API_KEY",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
    )

    with pytest.raises(RuntimeError, match="MISSING_API_KEY"):
        adapter.generate("hello")


def test_http_adapter_parses_openai_compatible_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [{"message": {"content": "remote answer"}}],
                    "usage": {"prompt_tokens": 7, "completion_tokens": 3},
                }
            ).encode("utf-8")

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.get_header("Authorization")
        return FakeResponse()

    monkeypatch.setenv("REMOTE_API_KEY", "top-secret")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    adapter = OpenAICompatibleHTTPAdapter(
        _model_name="remote-model",
        _provider="remote",
        endpoint="https://example.invalid/v1/chat/completions",
        api_key_env="REMOTE_API_KEY",
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.02,
        timeout_s=12,
    )

    result = adapter.generate("hello remote model")

    assert result.response == "remote answer"
    assert result.token_usage.input_tokens == 7
    assert result.token_usage.output_tokens == 3
    assert result.estimated_cost_usd == pytest.approx(0.00013)
    assert captured["timeout"] == 12
    assert captured["body"]["model"] == "remote-model"
    assert captured["body"]["messages"][0]["content"] == "hello remote model"
    assert captured["authorization"] == "Bearer top-secret"


def test_http_adapter_wraps_transport_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, timeout: float) -> object:
        raise urllib.error.URLError("network down")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    adapter = OpenAICompatibleHTTPAdapter(
        _model_name="remote-model",
        _provider="remote",
        endpoint="https://example.invalid/v1/chat/completions",
        api_key_env=None,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
    )

    with pytest.raises(RuntimeError, match="Model request failed"):
        adapter.generate("hello")