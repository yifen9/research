from __future__ import annotations

from pathlib import Path

from research.io.text import read_text, write_text


def memory_path(root: Path, role: str) -> Path:
    return root / "out" / "agent" / "memory" / f"{role}.md"


def write_memory(root: Path, role: str, text: str) -> Path:
    return write_text(memory_path(root, role), text)


def read_memory(root: Path, role: str) -> str:
    return read_text(memory_path(root, role))
