from __future__ import annotations

import argparse
from pathlib import Path

from .experiment import run_from_config
from .log import configure_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run model routing experiments.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.example.json"),
        help="Path to experiment configuration JSON.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Structured log level.",
    )
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    paths = run_from_config(args.config)
    print(f"Wrote {paths['jsonl']}")
    print(f"Wrote {paths['csv']}")
    print(f"Wrote {paths['summary']}")
    return 0

