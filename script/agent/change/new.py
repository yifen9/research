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


def read_state(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def check_worker(session_dir: Path, worker: str) -> dict[str, Any]:
    path = session_dir / worker / "state.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    data = read_state(path)

    if data["role"] != "worker":
        raise ValueError("session is not worker")

    if data["status"] == "retired":
        raise ValueError("worker is retired")

    return data


def task_text(title: str, change: str, worker: str) -> str:
    body: list[str] = []

    body.append("# Task\n")
    body.append("## Title\n")
    body.append(title)
    body.append("\n## Change\n")
    body.append(f"- id: {change}")
    body.append(f"- worker: {worker}")
    body.append("\n## Objective\n")
    body.append("To be filled by the human before assigning the task to a worker.\n")
    body.append("## Scope\n")
    body.append("- To be filled.\n")
    body.append("## Required Command\n")
    body.append("- To be filled.\n")
    body.append("## Expected Output\n")
    body.append("- To be filled.")
    body.append("")

    return "\n".join(body)


def proposal_text(change: str, worker: str) -> str:
    body: list[str] = []

    body.append("# Proposal\n")
    body.append("## Change\n")
    body.append(f"- id: {change}")
    body.append(f"- worker: {worker}")
    body.append("\n## Task\n")
    body.append("To be filled by the worker.\n")
    body.append("## Summary\n")
    body.append("To be filled by the worker.\n")
    body.append("## Changed File\n")
    body.append("- To be filled by the worker.\n")
    body.append("## Implementation Note\n")
    body.append("- To be filled by the worker.\n")
    body.append("## Command\n")
    body.append("- To be filled by the worker.\n")
    body.append("## Result\n")
    body.append("- To be filled by the worker.\n")
    body.append("## Risk\n")
    body.append("- To be filled by the worker.\n")
    body.append("## Reviewer Checklist\n")
    body.append("- To be filled by the worker.")
    body.append("")

    return "\n".join(body)


def review_text(change: str, worker: str) -> str:
    body: list[str] = []

    body.append("# Review\n")
    body.append("## Change\n")
    body.append(f"- id: {change}")
    body.append(f"- worker: {worker}")
    body.append("\n## Status\n")
    body.append("To be filled by the reviewer.\n")
    body.append("## Reason\n")
    body.append("To be filled by the reviewer.\n")
    body.append("## Risk\n")
    body.append("To be filled by the reviewer.\n")
    body.append("## Checked File\n")
    body.append("- To be filled by the reviewer.\n")
    body.append("## Checked Command\n")
    body.append("- To be filled by the reviewer.\n")
    body.append("## Required Change\n")
    body.append("- To be filled by the reviewer.\n")
    body.append("## Recommendation\n")
    body.append("To be filled by the reviewer.")
    body.append("")

    return "\n".join(body)


def result_data(change: str, title: str, worker: str, run_dir: str) -> dict[str, Any]:
    return {
        "change": change,
        "title": title,
        "status": "draft",
        "worker": worker,
        "reviewer": None,
        "risk": None,
        "commit": None,
        "run": run_dir,
    }


def write_change(
    target: Path,
    title: str,
    change: str,
    worker: str,
    run_dir: str,
) -> list[Path]:
    path = target / change

    if path.exists():
        raise FileExistsError(str(path))

    path.mkdir(parents=True, exist_ok=False)

    output: list[Path] = []

    output.append(write_text(path / "task.md", task_text(title, change, worker)))
    output.append(write_text(path / "proposal.md", proposal_text(change, worker)))
    output.append(write_text(path / "review.md", review_text(change, worker)))
    output.append(
        write_text(
            path / "result.yaml", yaml_text(result_data(change, title, worker, run_dir))
        )
    )

    return output


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
        raise ValueError("usage: new.py ROOT CHANGE_DIR SESSION_DIR TITLE WORKER")

    root = Path(argv[1]).resolve()
    target = Path(argv[2])
    session_dir = Path(argv[3])
    title = argv[4]
    worker = argv[5]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    check_worker(session_dir, worker)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "target": str(target),
            "session_dir": str(session_dir),
            "title": title,
            "worker": worker,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        change = Path(run.run_dir).name

        run.logger.info(
            jline(
                "script",
                "change",
                "start",
                {
                    "root": str(root),
                    "target": str(target),
                    "session_dir": str(session_dir),
                    "title": title,
                    "worker": worker,
                    "change": change,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_change(target, title, change, worker, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "change",
                "ok",
                {
                    "change": change,
                    "worker": worker,
                    "output": len(output),
                    "target": str(target),
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "change": change,
                "title": title,
                "worker": worker,
                "target": str(target),
                "output": len(output),
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
    ) as error:
        fail(run, "change", error)


if __name__ == "__main__":
    main(sys.argv)
