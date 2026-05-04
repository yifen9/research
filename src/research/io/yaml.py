from __future__ import annotations

from typing import Any

import yaml


def format_yaml(data: Any) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=True,
        allow_unicode=True,
        default_flow_style=False,
    )


def write_yaml(path: str, data: Any) -> str:
    text = format_yaml(data)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
        if not text.endswith("\n"):
            file.write("\n")
    return path


def read_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)
