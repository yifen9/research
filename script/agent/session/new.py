from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def check_role(role: str) -> None:
    allow = {"worker", "reviewer", "human"}

    if role not in allow:
        raise ValueError(f"invalid role: {role}")


def state_data(session: str, role: str, run_dir: str) -> dict[str, Any]:
    return {
        "session": session,
        "role": role,
        "status": "init",
        "threshold": 0.5,
        "task_count": 0,
        "accept_count": 0,
        "reject_count": 0,
        "pass_rate": None,
        "created_run": run_dir,
        "memory": "memory.md",
        "summary": "_summary.md",
    }


def memory_text(session: str, role: str) -> str:
    body: list[str] = []

    body.append("# Session Memory\n")
    body.append("## Session\n")
    body.append(f"- session: {session}")
    body.append(f"- role: {role}")
    body.append("\n## Task History\n")
    body.append("None.\n")
    body.append("## Accepted Change\n")
    body.append("None.\n")
    body.append("## Rejected Change\n")
    body.append("None.\n")
    body.append("## Common Failure\n")
    body.append("None.\n")
    body.append("## Useful Knowledge\n")
    body.append("None.\n")
    body.append("## Next Session Advice\n")
    body.append("None.")
    body.append("")

    return "\n".join(body)


def summary_text(data: dict[str, Any]) -> str:
    body: list[str] = []

    body.append("# Session Summary\n")
    body.append("## Status\n")
    body.append(f"- session: {data['session']}")
    body.append(f"- role: {data['role']}")
    body.append(f"- status: {data['status']}")
    body.append(f"- threshold: {data['threshold']}")
    body.append(f"- task_count: {data['task_count']}")
    body.append(f"- accept_count: {data['accept_count']}")
    body.append(f"- reject_count: {data['reject_count']}")
    body.append(f"- pass_rate: {data['pass_rate']}")
    body.append(f"- created_run: {data['created_run']}")
    body.append("\n## File\n")
    body.append("- state: state.yaml")
    body.append("- memory: memory.md")
    body.append("")

    return "\n".join(body)


def write_session(target: Path, role: str, session: str, run_dir: str) -> list[Path]:
    path = target / session

    if path.exists():
        raise FileExistsError(str(path))

    path.mkdir(parents=True, exist_ok=False)

    data = state_data(session, role, run_dir)
    output: list[Path] = []

    output.append(write_text(path / "state.yaml", yaml_text(data)))
    output.append(write_text(path / "memory.md", memory_text(session, role)))
    output.append(write_text(path / "_summary.md", summary_text(data)))

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
    if len(argv) != 4:
        raise ValueError("usage: new.py ROOT TARGET ROLE")

    root = Path(argv[1]).resolve()
    target = Path(argv[2])
    role = argv[3]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    check_role(role)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "target": str(target),
            "role": role,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        session = Path(run.run_dir).name

        run.logger.info(
            jline(
                "script",
                "session",
                "start",
                {
                    "root": str(root),
                    "target": str(target),
                    "role": role,
                    "session": session,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_session(target, role, session, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "session",
                "ok",
                {
                    "session": session,
                    "role": role,
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
                "session": session,
                "role": role,
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
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
