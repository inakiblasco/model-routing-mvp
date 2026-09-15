from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_routing_mvp.adapters import OpenAICompatibleHTTPAdapter, SyntheticModelAdapter
from model_routing_mvp.config import build_models, build_routers, load_config


def _base_config() -> dict[str, object]:
    data = json.loads(Path("config.example.json").read_text(encoding="utf-8"))
    data["benchmark_path"] = str(Path(str(data["benchmark_path"])).resolve())
    return data


def _write_config(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    data = _base_config()
    data["output_dir"] = "relative-output"

    config = load_config(_write_config(tmp_path, data))

    assert config.benchmark_path.is_absolute()
    assert config.output_dir == tmp_path / "relative-output"
    assert config.redact_model_responses is False


def test_environment_overrides_config_paths_and_redaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _base_config()
    benchmark = tmp_path / "tasks.jsonl"
    benchmark.write_text(
        '{"task_id":"t1","prompt":"What is 2 + 2?","expected_category":"simple"}\n',
        encoding="utf-8",
    )
    output_dir = tmp_path / "env-output"

    monkeypatch.setenv("MODEL_ROUTING_BENCHMARK_PATH", str(benchmark))
    monkeypatch.setenv("MODEL_ROUTING_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("MODEL_ROUTING_REDACT_RESPONSES", "true")

    config = load_config(_write_config(tmp_path, data))

    assert config.benchmark_path == benchmark
    assert config.output_dir == output_dir
    assert config.redact_model_responses is True


def test_build_models_supports_synthetic_and_endpoint_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _base_config()
    data["models"] = [
        {
            "key": "fast",
            "adapter": "synthetic",
            "provider": "local",
            "model_name": "fast-sim",
            "capabilities": ["simple"],
        },
        {
            "key": "strong",
            "adapter": "openai_compatible_http",
            "provider": "remote",
            "model_name": "remote-model",
            "endpoint_env": "REMOTE_ENDPOINT",
            "api_key_env": "REMOTE_API_KEY",
        },
    ]
    data["baselines"] = {"fast": "fast", "strong": "strong"}
    data["routes"] = {"simple": "fast", "coding": "strong", "reasoning": "strong"}
    data["policy"] = {"fast": "fast", "standard": "strong", "strong": "strong"}
    monkeypatch.setenv("REMOTE_ENDPOINT", "https://example.invalid/chat")

    models = build_models(load_config(_write_config(tmp_path, data)))

    assert isinstance(models["fast"], SyntheticModelAdapter)
    assert isinstance(models["strong"], OpenAICompatibleHTTPAdapter)
    assert models["strong"].endpoint == "https://example.invalid/chat"


def test_build_models_rejects_unknown_adapter(tmp_path: Path) -> None:
    data = _base_config()
    models = data["models"]
    assert isinstance(models, list)
    model = dict(models[0])
    model["adapter"] = "mystery"
    data["models"] = [model]

    with pytest.raises(ValueError, match="Unknown adapter"):
        build_models(load_config(_write_config(tmp_path, data)))


def test_build_routers_exposes_required_baselines(tmp_path: Path) -> None:
    routers = build_routers(load_config(_write_config(tmp_path, _base_config())))

    assert [router.name for router in routers] == [
        "always_fast",
        "always_strong",
        "rule_based_router",
        "policy_router",
    ]
