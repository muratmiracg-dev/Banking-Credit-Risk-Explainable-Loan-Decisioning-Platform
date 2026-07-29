#!/usr/bin/env python3
"""Local convenience wrapper for the package pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from credit_risk.pipeline import manifest_as_json, run_pipeline  # noqa: E402

if __name__ == "__main__":
    print(manifest_as_json(run_pipeline(ROOT)))
