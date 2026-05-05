from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.io.jsonl import append_jsonl


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def session_root(root: Path) -> Path:
    return root / "out" / "agent" / "session"


def session_dir(root: Path, role: str, name: str) -> Path:
    return session_root(root) / role / name


def event_file(root: Path, role: str, name: str) -> Path:
    return session_dir(root, role, name) / "event.jsonl"


def message_file(root: Path, role: str, name: str) -> Path:
    return session_dir(root, role, name) / "message.jsonl"


def append_event(root: Path, role: str, name: str, data: dict[str, Any]) -> Path:
    path = event_file(root, role, name)
    append_jsonl(str(path), data)
    return path


def append_message(root: Path, role: str, name: str, data: dict[str, Any]) -> Path:
    path = message_file(root, role, name)
    append_jsonl(str(path), data)
    return path
