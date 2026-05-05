from __future__ import annotations

from pathlib import Path
from typing import Any

from research.io.yaml import read_yaml


def read_config(root: Path) -> dict[str, Any]:
    path = root / "config" / "agent.yaml"
    return read_yaml(str(path))


def backend_name(data: dict[str, Any]) -> str:
    return data["backend"]["active"]
