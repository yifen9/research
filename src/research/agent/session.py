from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import os
from pathlib import Path
import re
import shutil
from typing import Any

from research.agent.audit import append_event, append_message, message_record, message_file, session_dir, utc_now
from research.agent.memory import write_memory
from research.agent.vector import add_heartbeat, add_message, check_store, missing_message, sync_message
from research.io.jsonl import read_jsonl
from research.io.text import write_text
from research.io.yaml import read_yaml, write_yaml


ROLE = {"architect"}
TEMPLATE_PART = ["Review", "Summary", "Next", "Risk", "Choice"]


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


def active_backend(root: Path, backend: str) -> None:
    data = read_yaml(str(root / "config" / "agent.yaml"))
    active = data["backend"]["active"]

    if active != backend:
        raise ValueError("backend mismatch")


def check_part(text: str, kind: str) -> None:
    for part in TEMPLATE_PART:
        if f"## {part}" not in text:
            raise ValueError(f"{kind} missing {part}")


def missing_part(text: str) -> list[str]:
    return [part for part in TEMPLATE_PART if f"## {part}" not in text]


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


def active_name(root: Path, role: str) -> str:
    role_ok(role)
    base = root / "out" / "agent" / "session" / role
    data: list[str] = []

    if not base.is_dir():
        raise ValueError("no active session")

    for path in sorted(base.iterdir()):
        if not path.is_dir():
            continue
        item = read_session(root, role, path.name)
        if item.get("state") == "active":
            data.append(path.name)

    if len(data) == 0:
        raise ValueError("no active session")

    if len(data) > 1:
        raise ValueError("multiple active sessions")

    return data[0]


def backend_active(root: Path) -> str:
    data = read_yaml(str(root / "config" / "agent.yaml"))
    return str(data["backend"]["active"])


def has_round(root: Path, role: str, name: str, source: str) -> bool:
    path = message_file(root, role, name)

    if not path.is_file():
        return False

    for item in read_jsonl(str(path)):
        if not isinstance(item, dict):
            continue
        if item.get("kind") == "round" and item.get("source") == source:
            return True

    return False


def source_path(root: Path, role: str, name: str, source: str) -> Path:
    key = sha256(source.encode("utf-8")).hexdigest()
    return session_dir(root, role, name) / "source" / f"{key}.lock"


def record_active(
    root: Path,
    role: str,
    user_text: str,
    ai_text: str,
    source: str,
    run: str,
) -> list[Path]:
    name = active_name(root, role)
    backend = backend_active(root)
    source = source.strip()
    path = source_path(root, role, name, source)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if has_round(root, role, name, source):
            return []
        raise ValueError("round locked")

    os.close(file)

    try:
        if has_round(root, role, name, source):
            return []
        return record_round(root, role, name, backend, user_text, ai_text, source, run)
    finally:
        path.unlink(missing_ok=True)


def record_round(
    root: Path,
    role: str,
    name: str,
    backend: str,
    user_text: str,
    ai_text: str,
    source: str,
    run: str,
) -> list[Path]:
    role_ok(role)
    active_backend(root, backend)
    data = read_session(root, role, name)

    if data["state"] != "active":
        raise ValueError("session not active")

    if not user_text.strip() or not ai_text.strip():
        raise ValueError("empty message")

    source = source.strip()
    if not source:
        raise ValueError("empty source")

    check_store(root, role, name)
    user_item = message_record("user", user_text, "round", run)
    ai_item = message_record("ai", ai_text, "round", run)
    round_id = sha256(
        f"{name}\n{run}\n{user_item['message_id']}\n{ai_item['message_id']}".encode("utf-8")
    ).hexdigest()
    output: list[Path] = []

    for part, item in [("user", user_item), ("ai", ai_item)]:
        item["round_id"] = round_id
        item["part"] = part
        item["source"] = source
        item["backend"] = backend

    for item in [user_item, ai_item]:
        output.append(append_message(root, role, name, item))

    for item in [user_item, ai_item]:
        add_message(root, role, name, item)

    return output


def bad_round(root: Path, role: str, name: str) -> list[str]:
    path = message_file(root, role, name)
    data: dict[str, list[str]] = {}

    if not path.is_file():
        return []

    for item in read_jsonl(str(path)):
        if not isinstance(item, dict):
            continue
        if item.get("kind") != "round":
            continue
        round_id = str(item.get("round_id", ""))
        part = str(item.get("part", ""))
        actor = str(item.get("actor", ""))
        source = str(item.get("source", ""))
        backend = str(item.get("backend", ""))
        if not round_id or part not in {"user", "ai"} or actor != part or not source.strip() or not backend:
            return ["round"]
        if round_id not in data:
            data[round_id] = []
        data[round_id].append(part)

    return [key for key, value in data.items() if sorted(value) != ["ai", "user"]]


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
    body.append("- config/template/agent/memory.md")
    body.append("- config/template/agent/handoff.md")
    body.append("- config/agent.yaml")
    body.append(f"- out/agent/memory/{role}.md when present")
    body.append(f"- out/agent/handoff/{role}.md when present")
    body.append("")
    body.append("## Cycle")
    body.append("- Review completed work")
    body.append("- Summarize current state")
    body.append("- Forecast risk and next choices")
    body.append("")
    body.append("## Mode")
    body.append("- Make mode explicit for durable work")
    body.append("- Stop at mode gates that require human choice")
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
    check_part(memory_text, "memory")
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

    if bad_round(root, role, name):
        bad.append("round")

    if (folder / "session.yaml").is_file():
        data = read_session(root, role, name)
        if data.get("state") == "closed":
            memory = folder / "memory.md"
            summary = folder / "summary.md"

            if not memory.is_file():
                bad.append("memory")
            elif missing_part(memory.read_text()):
                bad.append("memory")

            if not summary.is_file():
                bad.append("summary")

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

    handoff = root / "out" / "agent" / "handoff"
    if handoff.is_dir():
        for path in sorted(handoff.glob("*.md")):
            if missing_part(path.read_text()):
                bad[f"handoff/{path.stem}"] = ["handoff"]

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

    check_part(handoff_text, "handoff")
    close_output = close_session(root, role, name, memory_text, summary_text, run)
    handoff_file = write_handoff(root, role, handoff_text)
    new_name, new_output = make_session(root, role, topic, run)
    output: list[Path] = []
    output.extend(close_output)
    output.append(handoff_file)
    output.extend(new_output)
    return new_name, output
