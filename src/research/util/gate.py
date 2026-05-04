from __future__ import annotations

from pathlib import Path
import shlex
from typing import Any

from research.io.yaml import read_yaml
from research.util.git import run_cmd


def read_conf(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    if "agent" not in data:
        raise KeyError("agent")

    agent = data["agent"]

    if not isinstance(agent, dict):
        raise TypeError("agent")

    return agent


def gate_list(conf: dict[str, Any], name: str) -> list[str]:
    gate = conf["gate"]

    if not isinstance(gate, dict):
        raise TypeError("gate")

    data = gate[name]

    if not isinstance(data, list):
        raise TypeError(name)

    return [str(item) for item in data]


def run_gate(root: Path, conf: Path, name: str) -> dict[str, str]:
    agent = read_conf(conf)
    data = gate_list(agent, name)
    output: dict[str, str] = {}

    for item in data:
        args = shlex.split(item)
        output[item] = run_cmd(root, args)

    return output
