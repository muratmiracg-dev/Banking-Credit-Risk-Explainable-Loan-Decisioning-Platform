"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("config/project.yaml")


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Load the project YAML and enforce the non-production safety controls."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not config["project"]["synthetic_only"]:
        raise ValueError("This reference implementation only supports synthetic data.")
    if config["project"]["production_decisions_permitted"]:
        raise ValueError("Production credit decisions must remain disabled.")
    if config["policy"]["approve_max_pd"] >= config["policy"]["refer_max_pd"]:
        raise ValueError("approve_max_pd must be lower than refer_max_pd.")
    return config
