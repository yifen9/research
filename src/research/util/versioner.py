from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from research.io.json import read_json, write_json


def dir_ts(timestamp: str) -> str:
    date = datetime.fromisoformat(timestamp)
    return date.strftime("%Y%m%dT%H%M%S%f")


def make_dir(base: str, meta: dict[str, Any]) -> str:
    timestamp = dir_ts(meta["timestamp"])
    finger = meta["fingerprint"]
    path = os.path.join(base, f"{timestamp}_{finger}")
    os.makedirs(path, exist_ok=False)
    write_json(os.path.join(path, "_meta.json"), meta)
    return path


def list_meta(base: str) -> list[dict[str, Any]]:
    if not os.path.isdir(base):
        raise NotADirectoryError(base)

    data: list[dict[str, Any]] = []

    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name, "_meta.json")

        if os.path.isfile(path):
            item = read_json(path)

            if not isinstance(item, dict):
                raise TypeError(path)

            data.append(item)

    return data


def find_dir(base: str, meta: dict[str, Any]) -> str:
    if not os.path.isdir(base):
        raise NotADirectoryError(base)

    for name in sorted(os.listdir(base)):
        folder = os.path.join(base, name)
        path = os.path.join(folder, "_meta.json")

        if os.path.isfile(path) and read_json(path) == meta:
            return folder

    raise FileNotFoundError(base)
