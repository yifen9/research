from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.util.git import run_cmd
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def patch_path(change_dir: Path, change: str) -> Path:
    path = change_dir / change / "patch.diff"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path


def patch_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def changed_file(text: str) -> list[str]:
    data: list[str] = []

    for line in text.splitlines():
        if line.startswith("+++ b/"):
            data.append(line.removeprefix("+++ b/"))

    return data


def check_forbid(files: list[str]) -> None:
    forbid = {
        ".git",
        "out",
        ".venv",
        ".ruff_cache",
        "__pycache__",
    }

    for file in files:
        part = Path(file).parts

        for item in part:
            if item in forbid:
                raise ValueError(f"forbidden patch path: {file}")


def write_report(change_dir: Path, change: str, data: dict[str, Any]) -> Path:
    path = change_dir / change / "patch.yaml"
    return write_text(path, yaml_text(data))


def check_patch(root: Path, change_dir: Path, change: str) -> dict[str, Any]:
    path = patch_path(change_dir, change)
    text = patch_text(path)
    files = changed_file(text)

    if not files:
        raise ValueError("empty patch file list")

    check_forbid(files)
    output = run_cmd(root, ["git", "apply", "--check", str(path)])

    data = {
        "change": change,
        "patch": str(path),
        "status": "checked",
        "file": files,
        "output": output,
    }

    write_report(change_dir, change, data)
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
    if len(argv) != 4:
        raise ValueError("usage: check.py ROOT CHANGE_DIR CHANGE")

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
                "patch",
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

        data = check_patch(root, change_dir, change)

        run.logger.info(
            jline(
                "script",
                "patch",
                "ok",
                {
                    "change": change,
                    "status": data["status"],
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
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
        subprocess.CalledProcessError,
    ) as error:
        fail(run, "patch", error)


if __name__ == "__main__":
    main(sys.argv)
