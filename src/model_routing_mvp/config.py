from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapters import OpenAICompatibleHTTPAdapter, SyntheticModelAdapter
from .domain import ModelAdapter
from .routers import AlwaysRouter, RuleBasedRouter


@dataclass(frozen=True)
class ModelConfig:
    key: str
    adapter: str
    provider: str
    model_name: str
    capabilities: tuple[str, ...] = ()
    latency_ms: int = 0
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    endpoint: str = ""
    endpoint_env: str | None = None
    api_key_env: str | None = None
    timeout_s: float = 30


@dataclass(frozen=True)
class AppConfig:
    benchmark_path: Path
    output_dir: Path
    redact_model_responses: bool
    models: tuple[ModelConfig, ...]
    baselines: dict[str, str]
    routes: dict[str, str]


def load_config(path: Path) -> AppConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    base_dir = path.parent

    redact_default = bool(data.get("redact_model_responses", False))
    redact = _env_bool("MODEL_ROUTING_REDACT_RESPONSES", redact_default)

    benchmark_path = Path(
        os.environ.get("MODEL_ROUTING_BENCHMARK_PATH", data["benchmark_path"])
    )
    output_dir = Path(os.environ.get("MODEL_ROUTING_OUTPUT_DIR", data["output_dir"]))

    return AppConfig(
        benchmark_path=_resolve(base_dir, benchmark_path),
        output_dir=_resolve(base_dir, output_dir),
        redact_model_responses=redact,
        models=tuple(_model_config(item) for item in data["models"]),
        baselines=dict(data["baselines"]),
        routes=dict(data["routes"]),
    )


def build_models(config: AppConfig) -> dict[str, ModelAdapter]:
    models: dict[str, ModelAdapter] = {}
    for item in config.models:
        if item.adapter == "synthetic":
            models[item.key] = SyntheticModelAdapter(
                _model_name=item.model_name,
                _provider=item.provider,
                capabilities=frozenset(item.capabilities),
                latency_ms=item.latency_ms,
                input_cost_per_1k=item.input_cost_per_1k,
                output_cost_per_1k=item.output_cost_per_1k,
            )
        elif item.adapter == "openai_compatible_http":
            endpoint = (
                os.environ.get(item.endpoint_env, item.endpoint)
                if item.endpoint_env
                else item.endpoint
            )
            models[item.key] = OpenAICompatibleHTTPAdapter(
                _model_name=item.model_name,
                _provider=item.provider,
                endpoint=endpoint,
                api_key_env=item.api_key_env,
                input_cost_per_1k=item.input_cost_per_1k,
                output_cost_per_1k=item.output_cost_per_1k,
                timeout_s=item.timeout_s,
            )
        else:
            raise ValueError(f"Unknown adapter type: {item.adapter}")
    return models


def build_routers(config: AppConfig) -> tuple[AlwaysRouter | RuleBasedRouter, ...]:
    return (
        AlwaysRouter("always_fast", config.baselines["fast"]),
        AlwaysRouter("always_strong", config.baselines["strong"]),
        RuleBasedRouter(
            "rule_based_router",
            routes=config.routes,
            fallback_model_key=config.baselines["strong"],
        ),
    )


def _model_config(data: dict[str, Any]) -> ModelConfig:
    return ModelConfig(
        key=str(data["key"]),
        adapter=str(data["adapter"]),
        provider=str(data["provider"]),
        model_name=str(data["model_name"]),
        capabilities=tuple(str(item) for item in data.get("capabilities", ())),
        latency_ms=int(data.get("latency_ms", 0)),
        input_cost_per_1k=float(data.get("input_cost_per_1k", 0.0)),
        output_cost_per_1k=float(data.get("output_cost_per_1k", 0.0)),
        endpoint=str(data.get("endpoint", "")),
        endpoint_env=data.get("endpoint_env"),
        api_key_env=data.get("api_key_env"),
        timeout_s=float(data.get("timeout_s", 30)),
    )


def _resolve(base_dir: Path, path: Path) -> Path:
    return path if path.is_absolute() else base_dir / path


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}