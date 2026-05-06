from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from research.agent.backend import BackendSpec
from research.agent.registry import path_check


AUTO_ROUND_TARGET = "./.opencode/plugins/session-round.mjs"
AUTO_ROUND_COMMAND = ["uv", "run", "python", "script/agent/session/auto_round.py"]


def run_check(call: list[str]) -> int:
    result = subprocess.run(call, check=False, capture_output=True)
    return result.returncode


def source_path(root: Path, data: BackendSpec, template: str) -> Path:
    folder = path_check(root / "agent" / "backend", data.name) / "template"
    return path_check(folder, template)


def target_path(root: Path, target: str) -> Path:
    return path_check(root, target)


def check_render(root: Path, data: BackendSpec) -> list[str]:
    bad: list[str] = []

    for item in data.config:
        source = source_path(root, data, item.template)
        target = target_path(root, item.target)
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            bad.append(f"config:{item.target}")

    return bad


def good_value(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def round_data(root: Path) -> dict[str, Any] | None:
    path = target_path(root, "opencode.json")
    if not path.is_file():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    item_list = data.get("plugin")

    if not isinstance(item_list, list):
        return None

    for item in item_list:
        if (
            isinstance(item, list)
            and len(item) == 2
            and item[0] == AUTO_ROUND_TARGET
            and isinstance(item[1], dict)
        ):
            return item[1]

    return None


def round_check(root: Path, data: BackendSpec) -> list[str]:
    target = AUTO_ROUND_TARGET.removeprefix("./")
    config_target = {item.target for item in data.config}
    if target not in config_target:
        return ["auto-round:target"]

    item_data = round_data(root)
    if item_data is None:
        return ["auto-round:plugin"]

    bad: list[str] = []
    if item_data.get("role") != "architect":
        bad.append("auto-round:role")
    if item_data.get("source_prefix") != "opencode":
        bad.append("auto-round:source_prefix")
    if item_data.get("command") != AUTO_ROUND_COMMAND:
        bad.append("auto-round:command")
    if not good_value(item_data, "limit"):
        bad.append("auto-round:limit")
    if not good_value(item_data, "max_bytes"):
        bad.append("auto-round:max_bytes")

    return bad


def check_backend(root: Path, data: BackendSpec) -> list[str]:
    bad: list[str] = []

    bad.extend(check_render(root, data))
    bad.extend(round_check(root, data))

    for call in data.check:
        if run_check(call) != 0:
            bad.append("check:" + " ".join(call))

    return bad
