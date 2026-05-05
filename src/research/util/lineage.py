from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from research.io.json import read_json


@dataclass(slots=True)
class TraceNode:
    run_dir: str
    meta: dict[str, Any]
    field: str | None
    prev_dir: str | None


def meta_path(run_dir: str) -> str:
    return os.path.join(run_dir, "_meta.json")


def read_meta(run_dir: str) -> dict[str, Any]:
    path = meta_path(run_dir)
    data = read_json(path)
    if not isinstance(data, dict):
        raise TypeError(path)
    return data


def trace(run_dir: str, field: str, limit: int) -> list[TraceNode]:
    data: list[TraceNode] = []
    seen: set[str] = set()
    current = os.path.abspath(run_dir)

    for index in range(limit):
        if current in seen:
            raise RuntimeError(f"cycle at {current}")

        seen.add(current)
        path = meta_path(current)

        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        meta = read_meta(current)
        params = meta.get("params")
        prev: str | None = None

        if isinstance(params, dict):
            value = params.get(field)
            if isinstance(value, str) and value:
                prev = os.path.abspath(value)

        data.append(
            TraceNode(
                run_dir=current,
                meta=meta,
                field=field if prev is not None else None,
                prev_dir=prev,
            )
        )

        if prev is None:
            return data

        current = prev

    raise RuntimeError(f"limit at {limit}")


def trace_meta(run_dir: str, field: str, limit: int) -> list[dict[str, Any]]:
    return [item.meta for item in trace(run_dir, field, limit)]


def make_lineage(
    code: dict[str, Any],
    data: list[dict[str, Any]],
    env: dict[str, Any],
    seed: int,
    run: dict[str, Any],
) -> dict[str, Any]:
    return {
        "code": code,
        "data": data,
        "env": env,
        "seed": seed,
        "run": run,
    }
