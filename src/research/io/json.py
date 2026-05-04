from __future__ import annotations

import json
from typing import Any


def format_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)


def write_json(path: str, data: Any) -> str:
    text = format_json(data)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
        file.write("\n")
    return path


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
