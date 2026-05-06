from __future__ import annotations

from contextlib import contextmanager
import fcntl
from pathlib import Path
from typing import Iterator
from typing import Any

from research.agent.audit import append_event, message_file, redact_data, utc_now
from research.agent.registry import vector_conf, vector_kind, vector_path
from research.agent.store import Store, default_store, qdrant_store, store_key
from research.io.jsonl import read_jsonl


def read_conf(root: Path) -> dict[str, Any]:
    return vector_conf(root)


def make_store(root: Path, data: dict[str, Any]) -> Store:
    kind = vector_kind(root, data)

    path = vector_path(root, data)

    if kind == "local-jsonl":
        return default_store(path)

    if kind == "qdrant":
        collection = str(data["collection"])
        model = str(data["model"])
        return qdrant_store(path, collection, model)

    raise ValueError("unknown vector kind")


def lock_path(root: Path, data: dict[str, Any]) -> Path:
    kind = vector_kind(root, data)
    path = vector_path(root, data)

    if kind == "qdrant":
        return path / ".vector.lock"

    return path.with_name(f"{path.name}.lock")


@contextmanager
def vector_lock(root: Path, data: dict[str, Any]) -> Iterator[Path]:
    path = lock_path(root, data)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        try:
            yield path
        finally:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)


def log_event(
    root: Path, role: str, name: str, event: str, data: dict[str, Any]
) -> Path:
    item = dict(data)
    item["time"] = utc_now()
    item["event"] = event
    item["role"] = role
    item["name"] = name
    return append_event(root, role, name, item)


def check_store(root: Path, role: str, name: str) -> Store:
    data = read_conf(root)
    with vector_lock(root, data):
        store = make_store(root, data)
        try:
            store.connect()
            log_event(root, role, name, "vector-connect", {"backend": str(data["backend"])})
            return store
        except OSError as error:
            log_event(root, role, name, "vector-warning", {"error": str(error)})
            raise


def store_add(
    root: Path, role: str, name: str, data: dict[str, Any], text: str, meta: dict[str, Any]
) -> str:
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


def add_text(root: Path, role: str, name: str, text: str, meta: dict[str, Any]) -> str:
    data = read_conf(root)
    with vector_lock(root, data):
        return store_add(root, role, name, data, text, meta)


def add_heartbeat(root: Path, role: str, name: str, run: str, time: str) -> str:
    text = f"session heartbeat role={role} session={name} run={run} time={time}"
    meta = {"kind": "heartbeat", "session": name, "run": run, "time": time}
    return add_text(root, role, name, text, meta)


def message_meta(role: str, name: str, data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
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
    return text, meta


def message_add(
    root: Path, role: str, name: str, data: dict[str, Any], item: dict[str, Any]
) -> str:
    text, meta = message_meta(role, name, item)
    return store_add(root, role, name, data, text, meta)


def add_message(root: Path, role: str, name: str, data: dict[str, Any]) -> str:
    conf = read_conf(root)
    with vector_lock(root, conf):
        return message_add(root, role, name, conf, data)


def sync_message(root: Path, role: str, name: str) -> list[str]:
    path = message_file(root, role, name)
    if not path.is_file():
        return []

    data = read_conf(root)
    output: list[str] = []

    with vector_lock(root, data):
        store = make_store(root, data)
        for item in read_jsonl(str(path)):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", ""))
            meta = {"message_id": str(item.get("message_id", store_key(role, text, None)))}
            key = store_key(role, text, meta)
            if not store.has(key):
                output.append(message_add(root, role, name, data, item))

    return output


def missing_message(root: Path, role: str, name: str) -> list[str]:
    path = message_file(root, role, name)
    if not path.is_file():
        return []

    data = read_conf(root)
    output: list[str] = []

    with vector_lock(root, data):
        store = make_store(root, data)
        for item in read_jsonl(str(path)):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", ""))
            meta = {"message_id": str(item.get("message_id", store_key(role, text, None)))}
            key = store_key(role, text, meta)
            if not store.has(key):
                output.append(key)

    return output
