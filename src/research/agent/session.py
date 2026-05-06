from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
from typing import Any

from research.agent.audit import append_event, append_message, session_dir, utc_now
from research.agent.memory import write_memory
from research.agent.vector import add_heartbeat, add_message, check_store, missing_message, sync_message
from research.io.text import write_text
from research.io.yaml import read_yaml, write_yaml


ROLE = {"architect"}


def role_ok(role: str) -> None:
    if role not in ROLE:
        raise ValueError("unknown role")


def topic_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    if not slug:
        raise ValueError("empty topic")

    return slug


def make_name(time: str, topic: str) -> str:
    date = datetime.fromisoformat(time).strftime("%Y%m%dT%H%M%S")
    return f"{date}-{topic}"


def session_yaml(root: Path, role: str, name: str) -> Path:
    return session_dir(root, role, name) / "session.yaml"


def read_session(root: Path, role: str, name: str) -> dict[str, Any]:
    return read_yaml(str(session_yaml(root, role, name)))


def write_session(root: Path, role: str, name: str, data: dict[str, Any]) -> Path:
    return Path(write_yaml(str(session_yaml(root, role, name)), data))


def heartbeat(root: Path, role: str, name: str, run: str, time: str) -> Path:
    add_heartbeat(root, role, name, run, time)
    sync_message(root, role, name)
    event: dict[str, Any] = {
        "time": time,
        "event": "vector-heartbeat",
        "role": role,
        "name": name,
        "run": run,
    }
    return append_event(root, role, name, event)


def record_message(root: Path, role: str, name: str, data: dict[str, Any]) -> Path:
    path = append_message(root, role, name, data)
    add_message(root, role, name, data)
    return path


def initial_text(role: str) -> str:
    body: list[str] = []

    body.append("# Initial Context\n")
    body.append("## Read")
    body.append("- agent/agent.md")
    body.append(f"- agent/workflow/role/{role}.md")
    body.append(f"- agent/workflow/session/{role}.md")
    body.append("- agent/workflow/lifecycle.md")
    body.append("- agent/workflow/artifact.md")
    body.append("- agent/workflow/command.md")
    body.append("- config/rule/")
    body.append("- config/agent.yaml")
    body.append(f"- out/agent/memory/{role}.md when present")
    body.append(f"- out/agent/handoff/{role}.md when present")
    body.append("")
    body.append("## Cycle")
    body.append("- Review completed work")
    body.append("- Summarize current state")
    body.append("- Forecast risk and next choices")
    body.append("")

    return "\n".join(body)


def make_session(root: Path, role: str, topic: str, run: str) -> tuple[str, list[Path]]:
    role_ok(role)
    slug = topic_slug(topic)
    time = utc_now()
    name = make_name(time, slug)
    folder = session_dir(root, role, name)

    if folder.exists():
        raise FileExistsError(str(folder))

    folder.mkdir(parents=True, exist_ok=False)
    data: dict[str, Any] = {
        "id": name,
        "role": role,
        "topic": slug,
        "state": "active",
        "started": time,
        "closed": None,
        "run": run,
    }
    output: list[Path] = []
    output.append(write_session(root, role, name, data))
    output.append(write_text(folder / "initial.md", initial_text(role)))
    output.append(write_text(folder / "message.jsonl", ""))
    output.append(write_text(folder / "event.jsonl", ""))
    try:
        check_store(root, role, name)
        event: dict[str, Any] = {
            "time": time,
            "event": "session-new",
            "role": role,
            "name": name,
            "run": run,
        }
        output.append(append_event(root, role, name, event))
        output.append(heartbeat(root, role, name, run, time))
    except (FileNotFoundError, KeyError, OSError, TypeError, ValueError):
        shutil.rmtree(folder)
        raise
    return name, output


def close_session(
    root: Path,
    role: str,
    name: str,
    memory_text: str,
    summary_text: str,
    run: str,
) -> list[Path]:
    role_ok(role)
    data = read_session(root, role, name)

    if data["state"] != "active":
        raise ValueError("session not active")

    time = utc_now()
    data["state"] = "closed"
    data["closed"] = time
    folder = session_dir(root, role, name)
    output: list[Path] = []
    output.append(write_session(root, role, name, data))
    output.append(write_text(folder / "memory.md", memory_text))
    output.append(write_text(folder / "summary.md", summary_text))
    output.append(write_memory(root, role, memory_text))
    event: dict[str, Any] = {
        "time": time,
        "event": "session-close",
        "role": role,
        "name": name,
        "run": run,
    }
    output.append(append_event(root, role, name, event))
    return output


def retire_session(
    root: Path,
    role: str,
    name: str,
    reason: str,
    run: str,
) -> list[Path]:
    role_ok(role)
    data = read_session(root, role, name)
    time = utc_now()
    data["state"] = "retired"
    data["closed"] = time
    data["reason"] = reason
    output: list[Path] = []
    output.append(write_session(root, role, name, data))
    event: dict[str, Any] = {
        "time": time,
        "event": "session-retire",
        "role": role,
        "name": name,
        "reason": reason,
        "run": run,
    }
    output.append(append_event(root, role, name, event))
    return output


def check_session(root: Path, role: str, name: str) -> list[str]:
    bad: list[str] = []
    folder = session_dir(root, role, name)

    if not folder.is_dir():
        bad.append("dir")
        return bad

    for child in ["session.yaml", "initial.md", "message.jsonl", "event.jsonl"]:
        if not (folder / child).is_file():
            bad.append(child)

    try:
        check_store(root, role, name)
        if missing_message(root, role, name):
            bad.append("vector")
    except OSError:
        bad.append("vector")

    return bad


def scan_role(root: Path, role: Path) -> dict[str, list[str]]:
    bad: dict[str, list[str]] = {}

    if not role.is_dir():
        return bad

    for path in sorted(role.iterdir()):
        if not path.is_dir():
            continue

        data = check_session(root, role.name, path.name)

        if data:
            bad[f"{role.name}/{path.name}"] = data

    return bad


def scan_session(root: Path) -> dict[str, list[str]]:
    bad: dict[str, list[str]] = {}
    base = root / "out" / "agent" / "session"

    if not base.is_dir():
        return bad

    for role in sorted(base.iterdir()):
        bad.update(scan_role(root, role))

    return bad


def rotate_session(
    root: Path,
    role: str,
    name: str,
    memory_text: str,
    summary_text: str,
    handoff_text: str,
    topic: str,
    run: str,
) -> tuple[str, list[Path]]:
    from research.agent.handoff import write_handoff

    close_output = close_session(root, role, name, memory_text, summary_text, run)
    handoff_file = write_handoff(root, role, handoff_text)
    new_name, new_output = make_session(root, role, topic, run)
    output: list[Path] = []
    output.extend(close_output)
    output.append(handoff_file)
    output.extend(new_output)
    return new_name, output
