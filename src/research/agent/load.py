from __future__ import annotations

from pathlib import Path
from typing import Any

from research.agent.backend import BackendSpec, ConfigItem
from research.io.yaml import read_yaml


def read_manifest(root: Path, name: str) -> dict[str, Any]:
    path = root / "agent" / "backend" / name / "manifest.yaml"
    return read_yaml(str(path))


def parse_item(data: dict[str, Any]) -> ConfigItem:
    return ConfigItem(target=data["target"], template=data["template"])


def parse_backend(data: dict[str, Any]) -> BackendSpec:
    config = [parse_item(item) for item in data["config"]]
    return BackendSpec(
        name=data["name"],
        part=data["part"],
        config=config,
        check=data["check"],
    )


def load_backend(root: Path, name: str) -> BackendSpec:
    return parse_backend(read_manifest(root, name))
