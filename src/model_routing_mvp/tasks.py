from __future__ import annotations

import json
from pathlib import Path

from .domain import Task


_REQUIRED_FIELDS = {"task_id", "prompt", "expected_category"}


def load_tasks(path: Path) -> list[Task]:
    tasks: list[Task] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path} at line {line_number}") from exc

        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(
                f"Missing required task fields in {path} at line {line_number}: {fields}"
            )

        tasks.append(
            Task(
                task_id=str(data["task_id"]),
                prompt=str(data["prompt"]),
                expected_category=str(data["expected_category"]),
                evaluator=data.get("evaluator"),
            )
        )
    if not tasks:
        raise ValueError(f"No tasks found in {path}")
    return tasks