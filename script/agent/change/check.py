from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.io.text import read_text, write_text
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def section_text(text: str, name: str) -> str:
    lines = text.splitlines()
    start = -1
    body: list[str] = []

    for idx, line in enumerate(lines):
        if line.strip() == f"## {name}":
            start = idx + 1
            break

    if start < 0:
        raise KeyError(name)

    for line in lines[start:]:
        if line.startswith("## "):
            break

        body.append(line)

    return "\n".join(body).strip()


def check_field(text: str, name: str) -> None:
    value = section_text(text, name)

    if not value:
        raise ValueError(f"empty field: {name}")

    if "To be filled" in value:
        raise ValueError(f"placeholder field: {name}")


def check_task(change_dir: Path, change: str) -> dict[str, Any]:
    path = change_dir / change / "task.md"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    text = read_text(path)

    check_field(text, "Title")
    check_field(text, "Objective")
    check_field(text, "Scope")
    check_field(text, "Required Command")
    check_field(text, "Expected Output")

    data = {
        "change": change,
        "path": str(path),
        "status": "checked",
    }

    write_text(change_dir / change / "task.yaml", yaml_text(data))
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
                "task",
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

        data = check_task(change_dir, change)

        run.logger.info(
            jline(
                "script",
                "task",
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
    ) as error:
        fail(run, "task", error)


if __name__ == "__main__":
    main(sys.argv)
