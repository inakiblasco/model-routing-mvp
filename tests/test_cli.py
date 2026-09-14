from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_routing_mvp.cli import main


def test_cli_runs_experiment_and_prints_outputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = json.loads(Path("config.example.json").read_text(encoding="utf-8"))
    data["benchmark_path"] = str(Path(str(data["benchmark_path"])).resolve())
    data["output_dir"] = str(tmp_path / "outputs")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["--config", str(config_path), "--log-level", "WARNING"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "results.jsonl" in captured.out
    assert (tmp_path / "outputs" / "summary.md").exists()