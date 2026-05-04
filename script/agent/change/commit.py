from __future__ import annotations

from pathlib import Path
import re
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


def write_data(path: Path, data: dict[str, Any]) -> Path:
    return write_text(path, yaml_text(data))


def check_hash(commit: str) -> None:
    if re.fullmatch(r"[0-9a-fA-F]{7,40}", commit) is None:
        raise ValueError(f"invalid commit: {commit}")


def read_result(change_dir: Path, change: str) -> tuple[Path, dict[str, Any]]:
    path = change_dir / change / "result.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path, read_data(path)


def check_state(data: dict[str, Any]) -> None:
    if data["status"] != "approved":
        raise ValueError("commit requires approved change")


def apply_commit(
    change_dir: Path,
    change: str,
    commit: str,
    run_dir: str,
) -> dict[str, Any]:
    check_hash(commit)
    path, data = read_result(change_dir, change)
    check_state(data)

    data["status"] = "committed"
    data["commit"] = commit
    data["commit_run"] = run_dir

    write_data(path, data)
    return data


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
    if len(argv) != 5:
        raise ValueError("usage: commit.py ROOT CHANGE_DIR CHANGE COMMIT")

    root = Path(argv[1]).resolve()
    change_dir = Path(argv[2])
    change = argv[3]
    commit = argv[4]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "change_dir": str(change_dir),
            "change": change,
            "commit": commit,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "commit",
                "start",
                {
                    "root": str(root),
                    "change_dir": str(change_dir),
                    "change": change,
                    "commit": commit,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = apply_commit(change_dir, change, commit, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "commit",
                "ok",
                {
                    "change": change,
                    "status": data["status"],
                    "commit": commit,
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "change": change,
                "status": data["status"],
                "commit": commit,
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
        fail(run, "commit", error)


if __name__ == "__main__":
    main(sys.argv)
