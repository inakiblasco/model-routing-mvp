from __future__ import annotations

from pathlib import Path

import pytest

from model_routing_mvp.tasks import load_tasks


def test_load_tasks_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "tasks.jsonl"
    path.write_text(
        '\n{"task_id":"t1","prompt":"Prompt","expected_category":"simple"}\n\n',
        encoding="utf-8",
    )

    tasks = load_tasks(path)

    assert len(tasks) == 1
    assert tasks[0].task_id == "t1"
    assert tasks[0].evaluator is None
    assert tasks[0].task_type == "simple"
    assert tasks[0].risk == "low"
    assert tasks[0].sensitivity == "public"


def test_load_tasks_supports_phase1_labels(tmp_path: Path) -> None:
    path = tmp_path / "tasks.jsonl"
    path.write_text(
        (
            '{"task_id":"t1","prompt":"Prompt","expected_category":"simple",'
            '"task_type":"admin","risk":"high","sensitivity":"confidential"}\n'
        ),
        encoding="utf-8",
    )

    task = load_tasks(path)[0]

    assert task.task_type == "admin"
    assert task.risk == "high"
    assert task.sensitivity == "confidential"


def test_load_tasks_rejects_empty_benchmark(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("\n", encoding="utf-8")

    with pytest.raises(ValueError, match="No tasks found"):
        load_tasks(path)


def test_load_tasks_reports_invalid_json_line(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"task_id": "t1"\n', encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        load_tasks(path)


def test_load_tasks_reports_missing_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    path.write_text('{"task_id":"t1","prompt":"Prompt"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="expected_category"):
        load_tasks(path)
