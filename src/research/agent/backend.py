from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConfigItem:
    target: str
    template: str


@dataclass(slots=True)
class BackendSpec:
    name: str
    part: str
    config: list[ConfigItem]
    check: list[list[str]]
