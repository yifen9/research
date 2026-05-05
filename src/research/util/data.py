from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from research.io.json import read_json, write_json
from research.io.yaml import read_yaml


def source_path(base: Path) -> Path:
    return base / "SOURCE.yaml"


def meta_path(base: Path) -> Path:
    return base / "_meta.json"


def read_source(base: Path) -> dict[str, Any]:
    return read_yaml(str(source_path(base)))


def data_list(base: Path) -> list[Path]:
    output: list[Path] = []

    for path in sorted(base.rglob("*")):
        if path.is_file() and path.name not in {"SOURCE.yaml", "_meta.json"}:
            output.append(path)

    return output


def data_sha(base: Path) -> str:
    hasher = hashlib.sha256()

    for path in data_list(base):
        rel = path.relative_to(base).as_posix().encode("utf-8")
        hasher.update(rel)
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")

    return hasher.hexdigest()


def make_meta(base: Path, timestamp: str) -> dict[str, Any]:
    source = read_source(base)
    return {
        "source": source["name"],
        "version": source["version"],
        "url": source["url"],
        "license": source["license"],
        "sha": data_sha(base),
        "timestamp": timestamp,
    }


def write_meta(base: Path, timestamp: str) -> Path:
    meta = make_meta(base, timestamp)
    path = meta_path(base)
    write_json(str(path), meta)
    return path


def find_kind(base: Path) -> list[Path]:
    output: list[Path] = []

    if not base.is_dir():
        return output

    for source in sorted(base.iterdir()):
        if not source.is_dir():
            continue

        for path in sorted(source.iterdir()):
            if path.is_dir() and (path / "_meta.json").is_file():
                output.append(path)

    return output


def find_slug(slug: Path) -> list[Path]:
    output: list[Path] = []

    if not slug.is_dir():
        return output

    for kind in ["external", "pipeline"]:
        output.extend(find_kind(slug / "data" / kind))

    return output


def find_data(root: Path) -> list[Path]:
    output: list[Path] = []
    base = root / "project"

    if not base.is_dir():
        return output

    for slug in sorted(base.iterdir()):
        output.extend(find_slug(slug))

    return output


def check_path(base: Path) -> str:
    meta = read_json(str(meta_path(base)))

    if not isinstance(meta, dict):
        return "bad meta"

    if meta["sha"] != data_sha(base):
        return "sha mismatch"

    return ""


def check_data(root: Path) -> dict[str, str]:
    bad: dict[str, str] = {}

    for path in find_data(root):
        result = check_path(path)

        if result:
            bad[str(path)] = result

    return bad
