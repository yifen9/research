from __future__ import annotations

from pathlib import Path

from research.agent.backend import BackendSpec, ConfigItem
from research.io.text import read_text, write_text


def render_item(root: Path, name: str, item: ConfigItem) -> Path:
    source = root / "agent" / "backend" / name / "template" / item.template
    output = root / item.target
    return write_text(output, read_text(source))


def render_backend(root: Path, data: BackendSpec) -> list[Path]:
    output: list[Path] = []

    for item in data.config:
        output.append(render_item(root, data.name, item))

    return output
