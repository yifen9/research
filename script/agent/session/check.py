from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.text import read_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def has_text(path: Path) -> bool:
    if not path.is_file():
        return False

    return bool(read_text(path).strip())


def check_item(root: Path, path: Path) -> list[dict[str, Any]]:
    bad: list[dict[str, Any]] = []
    data = read_map(path / "session.yaml")
    state = data["state"]

    if state not in {"active", "closed", "retired"}:
        bad.append({"path": str(path), "kind": "state", "name": state})

    if state == "closed":
        for name in ["memory.md", "summary.md", "close.yaml"]:
            if not has_text(path / name):
                bad.append({"path": str(path / name), "kind": "missing", "name": name})

        if "handoff" in data and not has_text(path / str(data["handoff"])):
            bad.append({"path": str(path / str(data["handoff"])), "kind": "handoff"})

        if "role_memory" in data and not has_text(root / data["role_memory"]):
            bad.append({"path": str(data["role_memory"]), "kind": "memory"})

        if "role_handoff" in data and not has_text(root / data["role_handoff"]):
            bad.append({"path": str(data["role_handoff"]), "kind": "handoff"})

    if state == "retired":
        if not has_text(path / "retire.yaml"):
            bad.append({"path": str(path / "retire.yaml"), "kind": "retire"})

    return bad


def check_session(root: Path) -> list[dict[str, Any]]:
    base = root / "out" / "agent" / "session"

    if not base.exists():
        return []

    bad: list[dict[str, Any]] = []

    for role_dir in sorted(base.iterdir()):
        if not role_dir.is_dir():
            continue

        for folder in sorted(role_dir.iterdir()):
            if folder.is_dir():
                bad.extend(check_item(root, folder))

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
        bad = check_session(root)

        for item in bad:
            run.logger.error(jline("session", "check", "bad", item))

        if bad:
            raise RuntimeError("session check failed")

        run_ok(
            run,
            {
                "task": task,
                "bad_count": 0,
                "stat": {"total": 0},
            },
        )

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
