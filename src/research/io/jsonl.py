from __future__ import annotations

import json
from typing import Any, Iterable


def format_jsonl(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def append_jsonl(path: str, data: Any) -> str:
    with open(path, "a", encoding="utf-8") as file:
        file.write(format_jsonl(data))
        file.write("\n")
    return path


def write_jsonl(path: str, data: Iterable[Any]) -> str:
    with open(path, "w", encoding="utf-8") as file:
        for item in data:
            file.write(format_jsonl(item))
            file.write("\n")
    return path


def read_jsonl(path: str) -> list[Any]:
    data: list[Any] = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if text:
                data.append(json.loads(text))
    return data
