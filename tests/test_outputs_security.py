from __future__ import annotations

import csv
import json
import logging
from dataclasses import replace
from pathlib import Path

import pytest

from model_routing_mvp.config import load_config
from model_routing_mvp.domain import Task
from model_routing_mvp.experiment import run_experiment, write_outputs
from model_routing_mvp.tasks import load_tasks


_RESULT_KEYS = {
    "strategy",
    "task_id",
    "expected_category",
    "selected_model_key",
    "selected_model",
    "provider",
    "response",
    "latency_s",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost_usd",
    "evaluation_passed",
    "evaluation_score",
    "evaluation_details",
    "routing_reason",
}


def _records() -> list[dict[str, object]]:
    config = load_config(Path("config.example.json"))
    return run_experiment(config, load_tasks(config.benchmark_path))


def test_result_records_have_stable_schema_and_no_prompts() -> None:
    records = _records()

    assert records
    assert all(set(record) == _RESULT_KEYS for record in records)
    assert all("prompt" not in record for record in records)
    assert all(
        record["total_tokens"] == record["input_tokens"] + record["output_tokens"]
        for record in records
    )


def test_summary_contains_expected_strategy_metrics(tmp_path: Path) -> None:
    records = _records()
    write_outputs(tmp_path, records)

    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")

    assert "| always_fast | 6 | 33.33% | 0.200 | 0.000003 |" in summary
    assert "| always_strong | 6 | 100.00% | 1.800 | 0.000114 |" in summary
    assert "| rule_based_router | 6 | 100.00% | 0.933 | 0.000054 |" in summary


def test_jsonl_and_csv_outputs_round_trip(tmp_path: Path) -> None:
    records = _records()
    write_outputs(tmp_path, records)

    jsonl_rows = [
        json.loads(line)
        for line in (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    with (tmp_path / "results.csv").open(encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))

    assert len(jsonl_rows) == len(records) == 18
    assert len(csv_rows) == len(records)
    assert jsonl_rows[0]["task_id"] == csv_rows[0]["task_id"]


def test_redaction_keeps_evaluation_but_hides_recorded_responses() -> None:
    config = load_config(Path("config.example.json"))
    redacted_config = replace(config, redact_model_responses=True)

    records = run_experiment(redacted_config, load_tasks(config.benchmark_path))

    assert all(record["response"] == "[redacted]" for record in records)
    assert any(record["evaluation_passed"] for record in records)


def test_structured_logs_exclude_prompts_responses_and_credentials(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="model_routing_mvp.experiment")
    config = load_config(Path("config.example.json"))
    secret_prompt = "What is 2 + 2? DO_NOT_LOG_THIS_PROMPT_TOKEN"
    tasks = [
        Task(
            task_id="secret_task",
            prompt=secret_prompt,
            expected_category="simple",
            evaluator={"type": "exact", "value": "4"},
        )
    ]

    run_experiment(config, tasks)

    for record in caplog.records:
        assert "DO_NOT_LOG_THIS_PROMPT_TOKEN" not in record.getMessage()
        assert "prompt" not in record.__dict__
        assert "response" not in record.__dict__
        assert "api_key" not in record.__dict__
        assert "endpoint" not in record.__dict__