from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.gate import run_gate
from research.util.git import run_cmd
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


def patch_path(change_dir: Path, change: str) -> Path:
    path = change_dir / change / "patch.diff"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path


def result_path(change_dir: Path, change: str) -> Path:
    path = change_dir / change / "result.yaml"

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


def check_patch(root: Path, patch: Path) -> list[str]:
    text = patch_text(patch)
    files = changed_file(text)

    if not files:
        raise ValueError("empty patch file list")

    check_forbid(files)
    run_cmd(root, ["git", "apply", "--check", str(patch)])

    return files


def apply_patch(
    root: Path,
    change_dir: Path,
    config: Path,
    change: str,
    run_dir: str,
) -> dict[str, Any]:
    patch = patch_path(change_dir, change)
    result = result_path(change_dir, change)
    data = read_data(result)

    files = check_patch(root, patch)
    run_cmd(root, ["git", "apply", str(patch)])
    gate = run_gate(root, config, "approve")

    data["patch"] = {
        "status": "applied",
        "file": files,
        "run": run_dir,
    }
    data["gate"] = {name: "passed" for name in gate}

    write_data(result, data)

    report = {
        "change": change,
        "patch": str(patch),
        "status": "applied",
        "file": files,
        "gate": data["gate"],
    }

    write_text(change_dir / change / "patch.yaml", yaml_text(report))
    return report


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
        raise ValueError("usage: apply.py ROOT CHANGE_DIR CONFIG CHANGE")

    root = Path(argv[1]).resolve()
    change_dir = Path(argv[2])
    config = Path(argv[3])
    change = argv[4]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "change_dir": str(change_dir),
            "config": str(config),
            "change": change,
        },
        script=script,
        src=root / "src",
        config=config,
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
                    "config": str(config),
                    "change": change,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = apply_patch(root, change_dir, config, change, run.run_dir)

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
