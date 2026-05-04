from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def read_data(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def latest_dir(target: Path) -> Path:
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    data = [path for path in sorted(target.iterdir()) if path.is_dir()]

    if not data:
        raise FileNotFoundError(str(target))

    return data[-1]


def latest_session(target: Path, role: str) -> Path:
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    data: list[Path] = []

    for path in sorted(target.iterdir()):
        state = path / "state.yaml"

        if not state.is_file():
            continue

        item = read_data(state)

        if item["role"] != role:
            continue

        if item["status"] == "retired":
            continue

        data.append(path)

    if not data:
        raise FileNotFoundError(role)

    return data[-1]


def latest_change(target: Path) -> Path:
    return latest_dir(target)


def latest_bundle(target: Path) -> Path:
    return latest_dir(target)


def check_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(str(path))


def check_config(path: Path) -> dict[str, Any]:
    data = read_data(path)

    if "agent" not in data:
        raise KeyError("agent")

    agent = data["agent"]

    if not isinstance(agent, dict):
        raise TypeError("agent")

    if "mode" not in agent:
        raise KeyError("mode")

    if "gate" not in agent:
        raise KeyError("gate")

    return agent


def check_session(path: Path, role: str) -> dict[str, Any]:
    state = path / "state.yaml"
    memory = path / "memory.md"
    summary = path / "_summary.md"

    check_file(state)
    check_file(memory)
    check_file(summary)

    data = read_data(state)

    if data["role"] != role:
        raise ValueError(f"session is not {role}")

    if data["status"] == "retired":
        raise ValueError(f"{role} session is retired")

    return data


def check_change(path: Path) -> dict[str, Any]:
    check_file(path / "task.md")
    check_file(path / "proposal.md")
    check_file(path / "review.md")
    check_file(path / "result.yaml")

    data = read_data(path / "result.yaml")

    if "status" not in data:
        raise KeyError("status")

    if "worker" not in data:
        raise KeyError("worker")

    return data


def check_bundle(path: Path) -> None:
    check_file(path / "_manifest.md")
    check_file(path / "worker.md")
    check_file(path / "reviewer.md")


def smoke_data(
    config: Path,
    session_dir: Path,
    change_dir: Path,
    bundle_dir: Path,
) -> dict[str, Any]:
    agent = check_config(config)
    worker = latest_session(session_dir, "worker")
    reviewer = latest_session(session_dir, "reviewer")
    change = latest_change(change_dir)
    bundle = latest_bundle(bundle_dir)

    worker_data = check_session(worker, "worker")
    reviewer_data = check_session(reviewer, "reviewer")
    change_data = check_change(change)
    check_bundle(bundle)

    return {
        "mode": agent["mode"],
        "worker": worker.name,
        "worker_status": worker_data["status"],
        "reviewer": reviewer.name,
        "reviewer_status": reviewer_data["status"],
        "change": change.name,
        "change_status": change_data["status"],
        "change_worker": change_data["worker"],
        "bundle": bundle.name,
    }


def report_text(data: dict[str, Any]) -> str:
    body: list[str] = []

    body.append("# Human Smoke Report\n")
    body.append("## Status\n")
    body.append("passed\n")
    body.append("## Data\n")
    body.append("```yaml")
    body.append(yaml_text(data).rstrip())
    body.append("```")
    body.append("")

    return "\n".join(body)


def write_report(root: Path, data: dict[str, Any]) -> Path:
    path = root / "out" / "temp" / "agent" / "smoke" / "human.md"
    return write_text(path, report_text(data))


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
    if len(argv) != 6:
        raise ValueError(
            "usage: human.py ROOT CONFIG SESSION_DIR CHANGE_DIR BUNDLE_DIR"
        )

    root = Path(argv[1]).resolve()
    config = Path(argv[2])
    session_dir = Path(argv[3])
    change_dir = Path(argv[4])
    bundle_dir = Path(argv[5])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "config": str(config),
            "session_dir": str(session_dir),
            "change_dir": str(change_dir),
            "bundle_dir": str(bundle_dir),
        },
        script=script,
        src=root / "src",
        config=config,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "smoke",
                "start",
                {
                    "root": str(root),
                    "config": str(config),
                    "session_dir": str(session_dir),
                    "change_dir": str(change_dir),
                    "bundle_dir": str(bundle_dir),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = smoke_data(config, session_dir, change_dir, bundle_dir)
        report = write_report(root, data)

        run.logger.info(
            jline(
                "script",
                "smoke",
                "ok",
                {
                    "report": str(report),
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "report": str(report),
                **data,
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "smoke", error)


if __name__ == "__main__":
    main(sys.argv)
