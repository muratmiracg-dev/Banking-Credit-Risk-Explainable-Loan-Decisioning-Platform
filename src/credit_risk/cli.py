"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from credit_risk.pipeline import manifest_as_json, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic explainable credit risk pipeline."
    )
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--config", default="config/project.yaml", help="YAML config path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = run_pipeline(Path(args.root), args.config)
    print(manifest_as_json(manifest))


if __name__ == "__main__":
    main()
