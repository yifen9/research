from __future__ import annotations

from pathlib import Path
from typing import Any

from research.agent.registry import active_backend, read_config as read_agent


def read_config(root: Path) -> dict[str, Any]:
    return read_agent(root)


def backend_name(data: dict[str, Any]) -> str:
    active = data["backend"]["active"]

    if not isinstance(active, str):
        raise TypeError("backend")

    return active


def backend_active(root: Path) -> str:
    return active_backend(root)
