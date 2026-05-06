from __future__ import annotations

from pathlib import Path

from research.agent.backend import BackendSpec, ConfigItem
from research.agent.registry import path_check
from research.io.text import read_text, write_text


def render_item(root: Path, name: str, item: ConfigItem) -> Path:
    if Path(name).name != name:
        raise ValueError("bad backend")

    folder = path_check(root / "agent" / "backend", name) / "template"
    source = path_check(folder, item.template)
    output = path_check(root, item.target)
    return write_text(output, read_text(source))


def render_backend(root: Path, data: BackendSpec) -> list[Path]:
    output: list[Path] = []

    for item in data.config:
        output.append(render_item(root, data.name, item))

    return output
