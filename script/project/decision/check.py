from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


ROLE = {"architect", "manager", "reviewer", "worker"}
STATE = {"approved", "rejected"}
FIELD = {
    "id",
    "project",
    "kind",
    "state",
    "target",
    "actor",
    "role",
    "target_role",
    "decision",
    "reason",
    "time",
    "run",
    "branch",
    "base",
    "commit",
    "created",
    "updated",
}


def slug_ok(slug: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) is not None


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def bad_item(path: Path, kind: str, name: str) -> dict[str, Any]:
    return {"path": str(path), "kind": kind, "name": name}


def check_item(root: Path, path: Path) -> list[dict[str, Any]]:
    bad: list[dict[str, Any]] = []
    data = read_map(path)
    rel = path.relative_to(root)
    slug = rel.parts[1]
    name = rel.parts[3]

    for field in sorted(FIELD):
        if field not in data:
            bad.append(bad_item(path, "field", field))

    if data.get("project") != slug:
        bad.append(bad_item(path, "project", str(data.get("project"))))

    if data.get("id") != name:
        bad.append(bad_item(path, "id", str(data.get("id"))))

    if data.get("kind") != "decision":
        bad.append(bad_item(path, "kind", str(data.get("kind"))))

    if data.get("state") not in STATE:
        bad.append(bad_item(path, "state", str(data.get("state"))))

    if data.get("decision") != data.get("state"):
        bad.append(bad_item(path, "decision", str(data.get("decision"))))

    if data.get("role") not in ROLE:
        bad.append(bad_item(path, "role", str(data.get("role"))))

    if data.get("target_role") not in ROLE:
        bad.append(bad_item(path, "target_role", str(data.get("target_role"))))

    return bad


def check_decision(root: Path) -> list[dict[str, Any]]:
    base = root / "project"

    if not base.is_dir():
        return []

    bad: list[dict[str, Any]] = []

    for path in sorted(base.glob("*/decision/*/meta.yaml")):
        rel = path.relative_to(root)
        slug = rel.parts[1]
        name = rel.parts[3]

        if not slug_ok(slug):
            bad.append(bad_item(path, "slug", slug))

        if not slug_ok(name):
            bad.append(bad_item(path, "decision", name))

        bad.extend(check_item(root, path))

    return bad


def fail(run: Run, comp: str, error: BaseException) -> None:
    run.logger.error(
        jline(
            "script",
            comp,
            "error",
            {
                "type": type(error).__name__,
                "message": str(error),
                "run": run.run_dir,
            },
        )
    )
    run_err(run, error, {"comp": comp})
    raise error


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise ValueError("usage: check.py ROOT")

    root = Path(argv[1]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        bad = check_decision(root)

        for item in bad:
            run.logger.error(jline("decision", "check", "bad", item))

        if bad:
            raise RuntimeError("decision check failed")

        run_ok(run, {"task": task, "bad_count": 0, "stat": {"total": 0}})

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "decision", error)


if __name__ == "__main__":
    main(sys.argv)
