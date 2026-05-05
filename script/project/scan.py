from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def slug_ok(slug: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) is not None


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def bad_item(path: Path, kind: str, name: str) -> dict[str, Any]:
    return {"path": str(path), "kind": kind, "name": name}


def count_key(data: list[dict[str, Any]], key: str) -> dict[str, int]:
    output: dict[str, int] = {}

    for item in data:
        value = str(item[key])
        if value not in output:
            output[value] = 0
        output[value] += 1

    return dict(sorted(output.items()))


def check_file(path: Path, field: set[str]) -> list[dict[str, Any]]:
    bad: list[dict[str, Any]] = []
    data = read_map(path)

    for name in sorted(field):
        if name not in data:
            bad.append(bad_item(path, "field", name))

    if "state" in data and not str(data["state"]).strip():
        bad.append(bad_item(path, "state", "empty"))

    return bad


def field_stage() -> set[str]:
    return {
        "id",
        "project",
        "stage",
        "kind",
        "state",
        "title",
        "role",
        "run",
        "branch",
        "base",
        "target",
        "created",
        "updated",
    }


def field_experiment() -> set[str]:
    return {
        "id",
        "project",
        "stage",
        "experiment",
        "kind",
        "state",
        "title",
        "role",
        "run",
        "branch",
        "base",
        "target",
        "created",
        "updated",
    }


def field_result() -> set[str]:
    return {
        "id",
        "project",
        "experiment",
        "kind",
        "state",
        "worker",
        "role",
        "session",
        "run",
        "branch",
        "base",
        "target",
        "claim",
        "output",
        "check",
        "created",
        "updated",
    }


def field_review() -> set[str]:
    return {
        "id",
        "project",
        "kind",
        "target",
        "reviewer",
        "role",
        "decision",
        "reason",
        "risk",
        "run",
        "branch",
        "base",
        "created",
        "updated",
    }


def field_question() -> set[str]:
    return {
        "id",
        "project",
        "kind",
        "state",
        "role",
        "target_role",
        "target",
        "question",
        "run",
        "branch",
        "base",
        "created",
        "updated",
    }


def field_decision() -> set[str]:
    return {
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


def scan_kind(
    root: Path, slug: str, kind: str, field: set[str]
) -> list[dict[str, Any]]:
    bad: list[dict[str, Any]] = []
    base = root / "project" / slug / kind

    if not base.is_dir():
        return bad

    for path in sorted(base.glob("*/meta.yaml")):
        data = read_map(path)
        name = path.parent.name

        if not slug_ok(name):
            bad.append(bad_item(path, "slug", name))

        if data.get("project") != slug:
            bad.append(bad_item(path, "project", str(data.get("project"))))

        if data.get("kind") != kind:
            bad.append(bad_item(path, "kind", str(data.get("kind"))))

        bad.extend(check_file(path, field))

    return bad


def state_list(root: Path, slug: str, kind: str) -> list[dict[str, str]]:
    base = root / "project" / slug / kind
    data: list[dict[str, str]] = []

    if not base.is_dir():
        return data

    for path in sorted(base.glob("*/meta.yaml")):
        item = read_map(path)
        data.append({"id": path.parent.name, "state": str(item.get("state"))})

    return data


def scan_project(root: Path, slug: str) -> dict[str, Any]:
    if not slug_ok(slug):
        raise ValueError("bad slug")

    path = root / "project" / slug / "meta.yaml"
    data = read_map(path)

    if data.get("slug") != slug:
        raise ValueError("project slug mismatch")

    bad: list[dict[str, Any]] = []
    bad.extend(scan_kind(root, slug, "stage", field_stage()))
    bad.extend(scan_kind(root, slug, "experiment", field_experiment()))
    bad.extend(scan_kind(root, slug, "result", field_result()))
    bad.extend(scan_kind(root, slug, "review", field_review()))
    bad.extend(scan_kind(root, slug, "question", field_question()))
    bad.extend(scan_kind(root, slug, "decision", field_decision()))
    stage = state_list(root, slug, "stage")
    experiment = state_list(root, slug, "experiment")
    result = state_list(root, slug, "result")
    review = state_list(root, slug, "review")
    question = state_list(root, slug, "question")
    decision = state_list(root, slug, "decision")
    return {
        "project": slug,
        "bad": bad,
        "stage": stage,
        "experiment": experiment,
        "result": result,
        "review": review,
        "question": question,
        "decision": decision,
        "stat": {
            "stage": count_key(stage, "state"),
            "experiment": count_key(experiment, "state"),
            "result": count_key(result, "state"),
            "review": count_key(review, "state"),
            "question": count_key(question, "state"),
            "decision": count_key(decision, "state"),
        },
    }


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
    if len(argv) != 3:
        raise ValueError("usage: scan.py ROOT SLUG")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        data = scan_project(root, slug)

        for item in data["bad"]:
            run.logger.error(jline("project", "scan", "bad", item))

        if data["bad"]:
            raise RuntimeError("project scan failed")

        run_ok(run, data)

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "project", error)


if __name__ == "__main__":
    main(sys.argv)
