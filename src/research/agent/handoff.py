from __future__ import annotations

from pathlib import Path

from research.agent.registry import path_value, role_check
from research.io.text import read_text, write_text


def handoff_path(root: Path, role: str) -> Path:
    role_check(root, role)
    return path_value(root, "handoff") / f"{role}.md"


def write_handoff(root: Path, role: str, text: str) -> Path:
    return write_text(handoff_path(root, role), text)


def read_handoff(root: Path, role: str) -> str:
    return read_text(handoff_path(root, role))
