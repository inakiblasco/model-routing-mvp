from __future__ import annotations

import csv
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .config import AppConfig, build_models, build_routers, load_config
from .domain import EvaluationResult, GenerationResult, RouteDecision, Task
from .evaluation import evaluate
from .tasks import load_tasks

LOGGER = logging.getLogger(__name__)


def run_from_config(config_path: Path) -> dict[str, Path]:
    config = load_config(config_path)
    tasks = load_tasks(config.benchmark_path)
    records = run_experiment(config, tasks)
    write_outputs(config.output_dir, records)
    return {
        "jsonl": config.output_dir / "results.jsonl",
        "csv": config.output_dir / "results.csv",
        "summary": config.output_dir / "summary.md",
    }


def run_experiment(config: AppConfig, tasks: list[Task]) -> list[dict[str, Any]]:
    models = build_models(config)
    routers = build_routers(config)
    records: list[dict[str, Any]] = []

    for router in routers:
        for task in tasks:
            decision = router.route(task, models)
            model = models[decision.model_key]
            generation = model.generate(task.prompt)
            evaluation = evaluate(generation.response, task.evaluator)
            records.append(
                _record(
                    task=task,
                    decision=decision,
                    generation=generation,
                    evaluation=evaluation,
                    model_name=model.model_name,
                    provider=model.provider,
                    redact_response=config.redact_model_responses,
                )
            )
            LOGGER.info(
                "task_evaluated",
                extra={
                    "strategy": decision.strategy,
                    "task_id": task.task_id,
                    "selected_model": model.model_name,
                    "passed": evaluation.passed,
                    "latency_s": generation.latency_s,
                    "estimated_cost_usd": generation.estimated_cost_usd,
                },
            )

    return records


def write_outputs(output_dir: Path, records: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "results.jsonl", records)
    _write_csv(output_dir / "results.csv", records)
    (output_dir / "summary.md").write_text(_summary(records), encoding="utf-8")


def _record(
    *,
    task: Task,
    decision: RouteDecision,
    generation: GenerationResult,
    evaluation: EvaluationResult,
    model_name: str,
    provider: str,
    redact_response: bool,
) -> dict[str, Any]:
    usage = generation.token_usage
    return {
        "strategy": decision.strategy,
        "task_id": task.task_id,
        "expected_category": task.expected_category,
        "task_type": task.task_type or task.expected_category,
        "risk": task.risk,
        "sensitivity": task.sensitivity,
        "selected_model_key": decision.model_key,
        "selected_model": model_name,
        "provider": provider,
        "response": "[redacted]" if redact_response else generation.response,
        "latency_s": generation.latency_s,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "estimated_cost_usd": generation.estimated_cost_usd,
        "evaluation_passed": evaluation.passed,
        "evaluation_score": evaluation.score,
        "evaluation_details": evaluation.details,
        "routing_reason": decision.reason,
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def _summary(records: list[dict[str, Any]]) -> str:
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_strategy[str(record["strategy"])].append(record)

    lines = [
        "# Model Routing MVP Summary",
        "",
        "## Strategy Metrics",
        "",
        "| Strategy | Tasks | Success Rate | Avg Latency (s) | Avg Cost (USD) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for strategy, items in sorted(by_strategy.items()):
        total = len(items)
        successes = sum(1 for item in items if item["evaluation_passed"])
        avg_latency = sum(float(item["latency_s"]) for item in items) / total
        avg_cost = sum(float(item["estimated_cost_usd"]) for item in items) / total
        lines.append(
            f"| {strategy} | {total} | {successes / total:.2%} | "
            f"{avg_latency:.3f} | {avg_cost:.6f} |"
        )

    lines += [
        "",
        "## Routing Distribution",
        "",
        "| Strategy | Model | Count |",
        "| --- | --- | ---: |",
    ]
    for strategy, items in sorted(by_strategy.items()):
        distribution = Counter(str(item["selected_model"]) for item in items)
        for model_name, count in sorted(distribution.items()):
            lines.append(f"| {strategy} | {model_name} | {count} |")

    for field, title in (
        ("risk", "Risk Metrics"),
        ("sensitivity", "Sensitivity Metrics"),
        ("task_type", "Task Type Metrics"),
    ):
        lines += [
            "",
            f"## {title}",
            "",
            f"| Strategy | {field.replace('_', ' ').title()} | Tasks | Success Rate | Avg Cost (USD) |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
        for strategy, items in sorted(by_strategy.items()):
            by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for item in items:
                by_field[str(item[field])].append(item)
            for value, grouped in sorted(by_field.items()):
                total = len(grouped)
                successes = sum(1 for item in grouped if item["evaluation_passed"])
                avg_cost = (
                    sum(float(item["estimated_cost_usd"]) for item in grouped) / total
                )
                lines.append(
                    f"| {strategy} | {value} | {total} | "
                    f"{successes / total:.2%} | {avg_cost:.6f} |"
                )

    return "\n".join(lines) + "\n"
