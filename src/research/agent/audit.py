from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from research.agent.registry import path_value
from research.io.jsonl import append_jsonl


SAFE_MESSAGE_KEY = {
    "time",
    "run",
    "role",
    "name",
    "session",
    "actor",
    "kind",
    "event",
    "message_id",
    "round_id",
    "part",
    "source",
    "backend",
}
ROLE_RE = re.compile(r"[a-z][a-z0-9-]*")
SESSION_RE = re.compile(r"[0-9]{8}T[0-9]{6}-[a-z0-9]+(-[a-z0-9]+)*")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def session_root(root: Path) -> Path:
    return path_value(root, "session")


def check_role(role: str) -> None:
    if ROLE_RE.fullmatch(role) is None:
        raise ValueError("bad role")


def check_name(name: str) -> None:
    if SESSION_RE.fullmatch(name) is None:
        raise ValueError("bad session")


def session_dir(root: Path, role: str, name: str) -> Path:
    check_role(role)
    check_name(name)
    base = session_root(root).resolve()
    path = (base / role / name).resolve()

    if base != path and base not in path.parents:
        raise ValueError("bad session path")

    return path


def event_file(root: Path, role: str, name: str) -> Path:
    return session_dir(root, role, name) / "event.jsonl"


def message_file(root: Path, role: str, name: str) -> Path:
    return session_dir(root, role, name) / "message.jsonl"


def redact_text(text: str) -> str:
    value = re.sub(
        r"(?i)(password|passwd|pwd|secret|token|api[_-]?key)(\s*[:=]\s*)([^\s,;]+)",
        r"\1\2[REDACTED]",
        text,
    )
    value = re.sub(r"(?i)bearer\s+[a-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
    value = re.sub(r"\b[A-Za-z0-9_=-]{32,}\b", "[REDACTED]", value)
    return value


def redact_data(data: Any) -> Any:
    if isinstance(data, str):
        return redact_text(data)
    if isinstance(data, list):
        return [redact_data(item) for item in data]
    if isinstance(data, dict):
        output: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(key, str) and re.search(
                r"(?i)password|passwd|pwd|secret|token|api[_-]?key", key
            ):
                output[key] = "[REDACTED]"
            elif isinstance(key, str) and key in SAFE_MESSAGE_KEY:
                output[key] = value
            else:
                output[key] = redact_data(value)
        return output
    return data


def append_event(root: Path, role: str, name: str, data: dict[str, Any]) -> Path:
    path = event_file(root, role, name)
    append_jsonl(str(path), data)
    return path


def append_message(root: Path, role: str, name: str, data: dict[str, Any]) -> Path:
    path = message_file(root, role, name)
    append_jsonl(str(path), redact_data(data))
    return path


def message_record(actor: str, text: str, kind: str, run: str) -> dict[str, Any]:
    time = utc_now()
    data: dict[str, Any] = {
        "time": time,
        "message_id": uuid4().hex,
        "actor": actor,
        "kind": kind,
        "text": text,
    }
    data["run"] = run
    return data
