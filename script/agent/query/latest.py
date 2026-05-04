from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.yaml import read_yaml


def read_data(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def session_list(target: Path, role: str) -> list[str]:
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    data: list[str] = []

    for path in sorted(target.iterdir()):
        state = path / "state.yaml"

        if not state.is_file():
            continue

        item = read_data(state)

        if item["role"] != role:
            continue

        if item["status"] == "retired":
            continue

        data.append(path.name)

    return data


def active_change(status: str) -> set[str]:
    if status == "active":
        return {"draft", "accepted", "rejected", "returned", "approved"}

    if status == "any":
        return {
            "draft",
            "accepted",
            "rejected",
            "returned",
            "approved",
            "committed",
            "discarded",
        }

    return {status}


def change_list(target: Path, status: str) -> list[str]:
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    allow = active_change(status)
    data: list[str] = []

    for path in sorted(target.iterdir()):
        result = path / "result.yaml"

        if not result.is_file():
            continue

        item = read_data(result)

        if item["status"] in allow:
            data.append(path.name)

    return data


def latest(data: list[str]) -> str:
    if not data:
        raise FileNotFoundError("latest item not found")

    return data[-1]


def dir_list(target: Path) -> list[str]:
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    data: list[str] = []

    for path in sorted(target.iterdir()):
        if path.is_dir():
            data.append(path.name)

    return data


def main(argv: list[str]) -> None:
    if len(argv) != 5:
        raise ValueError("usage: latest.py ROOT TARGET KIND VALUE")

    target = Path(argv[2])
    kind = argv[3]
    value = argv[4]

    if kind == "session":
        print(latest(session_list(target, value)))
        return

    if kind == "change":
        print(latest(change_list(target, value)))
        return

    if kind == "dir":
        print(latest(dir_list(target)))
        return

    raise ValueError(f"invalid kind: {kind}")


if __name__ == "__main__":
    main(sys.argv)
