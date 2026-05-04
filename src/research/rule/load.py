from __future__ import annotations

from pathlib import Path
from typing import Any

from research.io.yaml import read_yaml


def load_rule(root: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}

    for path in sorted((root / "rule").glob("*.yaml")):
        data[path.stem] = read_yaml(str(path))

    return data


def load_word(root: Path) -> set[str]:
    pool: set[str] = set()
    word_dir = root / "rule" / "word"

    for path in sorted(word_dir.glob("*.yaml")):
        data = read_yaml(str(path))
        for word in data["word"]:
            pool.add(word)

    return pool


def read_index(root: Path) -> dict[str, Any]:
    path = root / "rule" / "index.yaml"
    return read_yaml(str(path))
