from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from research.io.yaml import read_yaml


ROLE_RE = re.compile(r"[a-z][a-z0-9-]*")


def read_registry(root: Path) -> dict[str, Any]:
    path = root / "config" / "rule" / "registry.yaml"
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    item = data["registry"]
    if not isinstance(item, dict):
        raise TypeError("registry")

    return item


def read_config(root: Path) -> dict[str, Any]:
    path = root / "config" / "agent.yaml"
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def role_list(root: Path) -> list[str]:
    data = read_registry(root)
    role = data["role"]
    value = role["allow"]

    if not isinstance(value, list):
        raise TypeError("role")

    return [str(item) for item in value]


def role_check(root: Path, role: str) -> None:
    if ROLE_RE.fullmatch(role) is None:
        raise ValueError("bad role")

    if role not in role_list(root):
        raise ValueError("unknown role")


def part_list(root: Path) -> list[str]:
    data = read_registry(root)
    role = data["role"]
    value = role["template_part"]

    if not isinstance(value, list):
        raise TypeError("template part")

    return [str(item) for item in value]


def path_check(root: Path, text: str) -> Path:
    item = Path(text)
    if item.is_absolute() or ".." in item.parts:
        raise ValueError("bad path")

    base = root.resolve()
    path = (base / item).resolve()
    if base != path and base not in path.parents:
        raise ValueError("bad path")

    return path


def path_value(root: Path, name: str) -> Path:
    data = read_registry(root)
    item = data["path"][name]

    if not isinstance(item, str):
        raise TypeError(name)

    return path_check(root, item)


def active_backend(root: Path) -> str:
    data = read_config(root)
    active = data["backend"]["active"]

    if not isinstance(active, str):
        raise TypeError("backend")

    return active


def vector_conf(root: Path) -> dict[str, Any]:
    data = read_config(root)
    item = data["session"]["vector"]

    if not isinstance(item, dict):
        raise TypeError("vector")

    vector_check(root, item)
    return item


def vector_item(root: Path, name: str) -> dict[str, Any]:
    data = read_registry(root)
    item = data["vector"]["allow"][name]

    if not isinstance(item, dict):
        raise TypeError(name)

    return item


def vector_check(root: Path, data: dict[str, Any]) -> None:
    backend = str(data["backend"])
    item = vector_item(root, backend)
    required = item["require"]

    if not isinstance(required, list):
        raise TypeError("require")

    for key in required:
        if key not in data:
            raise KeyError(str(key))

    fail = str(data["failure"])
    allow = read_registry(root)["vector"]["failure"]
    if fail not in allow:
        raise ValueError("bad vector failure")

    if data.get("required") is not True:
        raise ValueError("bad vector required")

    if fail != "fail":
        raise ValueError("bad vector failure")


def vector_kind(root: Path, data: dict[str, Any]) -> str:
    item = vector_item(root, str(data["backend"]))
    kind = item["kind"]

    if not isinstance(kind, str):
        raise TypeError("kind")

    return kind


def vector_path(root: Path, data: dict[str, Any]) -> Path:
    item = vector_item(root, str(data["backend"]))
    path = item["path"]

    if not isinstance(path, str):
        raise TypeError("path")

    return path_check(path_value(root, "vector"), path)
