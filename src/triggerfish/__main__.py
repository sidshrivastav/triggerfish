"""Triggerfish LSP Server entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import TriggerfishConfig
from .server import create_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triggerfish LSP server")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    parser.add_argument("--log-file", type=Path, help="Log file path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = TriggerfishConfig.default()
    config.log_level = args.log_level
    if args.log_file:
        config.log_file = args.log_file

    server = create_server(config)
    server.start_io()
    return 0


if __name__ == "__main__":
    sys.exit(main())
