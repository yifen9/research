from __future__ import annotations

from pathlib import Path
from typing import Any

from research.agent.audit import append_event, message_file, redact_data, utc_now
from research.agent.store import Store, default_store, qdrant_store, store_key
from research.io.jsonl import read_jsonl
from research.io.yaml import read_yaml


def read_conf(root: Path) -> dict[str, Any]:
    path = root / "config" / "agent.yaml"
    if not path.is_file():
        raise FileNotFoundError(str(path))
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    session = data.get("session")
    if not isinstance(session, dict):
        raise KeyError("session")

    vector = session.get("vector")
    if not isinstance(vector, dict):
        raise KeyError("vector")

    return vector


def make_store(root: Path, data: dict[str, Any]) -> Store:
    backend = str(data["backend"])

    if backend == "local-jsonl":
        return default_store(root)

    if backend == "qdrant-local":
        collection = str(data["collection"])
        model = str(data["model"])
        return qdrant_store(root, collection, model)

    raise ValueError("unknown vector backend")


def fail_kind(data: dict[str, Any]) -> str:
    if data.get("required") is True:
        return "fail"
    kind = str(data["failure"])
    if kind not in {"warn", "fail"}:
        raise ValueError("bad vector failure")
    return kind


def log_event(root: Path, role: str, name: str, event: str, data: dict[str, Any]) -> Path:
    item = dict(data)
    item["time"] = utc_now()
    item["event"] = event
    item["role"] = role
    item["name"] = name
    return append_event(root, role, name, item)


def check_store(root: Path, role: str, name: str) -> Store:
    data = read_conf(root)
    store = make_store(root, data)
    try:
        store.connect()
        log_event(root, role, name, "vector-connect", {"backend": str(data["backend"])})
        return store
    except OSError as error:
        log_event(root, role, name, "vector-warning", {"error": str(error)})
        raise


def add_text(root: Path, role: str, name: str, text: str, meta: dict[str, Any]) -> str:
    data = read_conf(root)
    store = make_store(root, data)
    try:
        key = store.add(role, text, meta)
        log_event(
            root,
            role,
            name,
            "vector-message",
            {"backend": str(data["backend"]), "id": key, "kind": str(meta["kind"])},
        )
        return key
    except OSError as error:
        log_event(root, role, name, "vector-warning", {"error": str(error)})
        raise


def add_heartbeat(root: Path, role: str, name: str, run: str, time: str) -> str:
    text = f"session heartbeat role={role} session={name} run={run} time={time}"
    meta = {"kind": "heartbeat", "session": name, "run": run, "time": time}
    return add_text(root, role, name, text, meta)


def add_message(root: Path, role: str, name: str, data: dict[str, Any]) -> str:
    item = redact_data(data)
    if not isinstance(item, dict):
        raise TypeError("message")
    text = str(item.get("text", ""))
    meta = {
        "kind": str(item.get("kind", "message")),
        "message_id": str(item.get("message_id", store_key(role, text, None))),
        "actor": str(item.get("actor", "")),
        "run": str(item.get("run", "")),
        "time": str(item.get("time", "")),
        "session": name,
    }
    for key in ["round_id", "part", "source", "backend"]:
        if key in item:
            meta[key] = str(item[key])
    return add_text(root, role, name, text, meta)


def sync_message(root: Path, role: str, name: str) -> list[str]:
    path = message_file(root, role, name)
    if not path.is_file():
        return []

    data = read_conf(root)
    store = make_store(root, data)
    output: list[str] = []

    for item in read_jsonl(str(path)):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", ""))
        meta = {"message_id": str(item.get("message_id", store_key(role, text, None)))}
        key = store_key(role, text, meta)
        if not store.has(key):
            output.append(add_message(root, role, name, item))

    return output


def missing_message(root: Path, role: str, name: str) -> list[str]:
    path = message_file(root, role, name)
    if not path.is_file():
        return []

    data = read_conf(root)
    store = make_store(root, data)
    output: list[str] = []

    for item in read_jsonl(str(path)):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", ""))
        meta = {"message_id": str(item.get("message_id", store_key(role, text, None)))}
        key = store_key(role, text, meta)
        if not store.has(key):
            output.append(key)

    return output
