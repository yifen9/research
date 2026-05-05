from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


ROLE = {"architect", "manager", "reviewer", "worker"}
STATE = {"claimed", "released"}
FIELD = {
    "id",
    "project",
    "experiment",
    "kind",
    "state",
    "role",
    "session",
    "run",
    "branch",
    "base",
    "target",
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


def session_path(root: Path, role: str, name: str) -> Path:
    return root / "out" / "agent" / "session" / role / name / "session.yaml"


def check_session(root: Path, path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    bad: list[dict[str, Any]] = []
    session = str(data.get("session"))
    role = str(data.get("role"))
    file = session_path(root, role, session)

    if file.is_file():
        item = read_map(file)
        if item.get("state") == "retired":
            bad.append(bad_item(path, "session", session))

    return bad


def check_claim(root: Path, path: Path) -> list[dict[str, Any]]:
    bad: list[dict[str, Any]] = []
    data = read_map(path)
    rel = path.relative_to(root)
    slug = rel.parts[1]
    experiment = rel.parts[3]

    for field in sorted(FIELD):
        if field not in data:
            bad.append(bad_item(path, "field", field))

    if data.get("project") != slug:
        bad.append(bad_item(path, "project", str(data.get("project"))))

    if data.get("experiment") != experiment:
        bad.append(bad_item(path, "experiment", str(data.get("experiment"))))

    if data.get("kind") != "experiment-claim":
        bad.append(bad_item(path, "kind", str(data.get("kind"))))

    if data.get("state") not in STATE:
        bad.append(bad_item(path, "state", str(data.get("state"))))

    if data.get("role") not in ROLE:
        bad.append(bad_item(path, "role", str(data.get("role"))))

    if data.get("target") != f"project/{slug}/experiment/{experiment}":
        bad.append(bad_item(path, "target", str(data.get("target"))))

    if data.get("state") == "released":
        for field in ["released", "release_role", "release_run", "reason"]:
            if field not in data:
                bad.append(bad_item(path, "field", field))

    bad.extend(check_session(root, path, data))
    return bad


def check_experiment(root: Path) -> list[dict[str, Any]]:
    base = root / "project"

    if not base.is_dir():
        return []

    bad: list[dict[str, Any]] = []

    for path in sorted(base.glob("*/experiment/*/claim.yaml")):
        rel = path.relative_to(root)
        slug = rel.parts[1]
        experiment = rel.parts[3]

        if not slug_ok(slug):
            bad.append(bad_item(path, "slug", slug))

        if not slug_ok(experiment):
            bad.append(bad_item(path, "experiment", experiment))

        bad.extend(check_claim(root, path))

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
        bad = check_experiment(root)

        for item in bad:
            run.logger.error(jline("experiment", "check", "bad", item))

        if bad:
            raise RuntimeError("experiment check failed")

        run_ok(run, {"task": task, "bad_count": 0, "stat": {"total": 0}})

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "experiment", error)


if __name__ == "__main__":
    main(sys.argv)
