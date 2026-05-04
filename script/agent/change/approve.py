from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.git import git_commit, run_cmd
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def read_data(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def write_data(path: Path, data: dict[str, Any]) -> Path:
    return write_text(path, yaml_text(data))


def latest_change(change_dir: Path, status: str) -> str:
    data: list[str] = []

    if not change_dir.is_dir():
        raise NotADirectoryError(str(change_dir))

    for path in sorted(change_dir.iterdir()):
        result = path / "result.yaml"

        if not result.is_file():
            continue

        item = read_data(result)

        if item["status"] == status:
            data.append(path.name)

    if not data:
        raise FileNotFoundError(f"{status} change not found")

    return data[-1]


def read_result(change_dir: Path, change: str) -> tuple[Path, dict[str, Any]]:
    path = change_dir / change / "result.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path, read_data(path)


def check_state(data: dict[str, Any]) -> None:
    if data["status"] != "accepted":
        raise ValueError("approve requires accepted change")


def apply_approve(root: Path, change_dir: Path, change: str, run_dir: str) -> dict[str, Any]:
    if change == "latest":
        change = latest_change(change_dir, "accepted")

    path, data = read_result(change_dir, change)
    check_state(data)

    fmt_out = run_cmd(root, ["just", "fmt"])
    check_out = run_cmd(root, ["just", "rule-check"])
    commit = git_commit(root, str(data["title"]))

    data["human"] = "approve"
    data["status"] = "committed"
    data["commit"] = commit
    data["decision_run"] = run_dir
    data["commit_run"] = run_dir
    data["check"] = {
        "fmt": "passed",
        "rule": "passed",
    }

    write_data(path, data)

    return {
        "change": change,
        "status": data["status"],
        "commit": commit,
        "fmt_output": fmt_out,
        "check_output": check_out,
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
    if len(argv) != 4:
        raise ValueError("usage: approve.py ROOT CHANGE_DIR CHANGE")

    root = Path(argv[1]).resolve()
    change_dir = Path(argv[2])
    change = argv[3]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "change_dir": str(change_dir),
            "change": change,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "approve",
                "start",
                {
                    "root": str(root),
                    "change_dir": str(change_dir),
                    "change": change,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = apply_approve(root, change_dir, change, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "approve",
                "ok",
                {
                    "change": data["change"],
                    "status": data["status"],
                    "commit": data["commit"],
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "change": data["change"],
                "status": data["status"],
                "commit": data["commit"],
            },
        )

    except (
        ValueError,
        KeyError,
        FileExistsError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
        subprocess.CalledProcessError,
    ) as error:
        fail(run, "approve", error)


if __name__ == "__main__":
    main(sys.argv)
