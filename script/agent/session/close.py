from __future__ import annotations

from pathlib import Path
import sys

from research.agent.session import close_session
from research.io.text import read_text
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


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
        raise ValueError("usage: close.py ROOT ROLE ID MEMORY SUMMARY")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    memory = Path(argv[4]).resolve()
    summary = Path(argv[5]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "role": role,
            "name": name,
            "memory": str(memory),
            "summary": str(summary),
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = close_session(
            root,
            role,
            name,
            read_text(memory),
            read_text(summary),
            run.run_dir,
        )
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "name": name,
                "output": [str(path) for path in output],
            },
        )

    except (ValueError, FileNotFoundError, KeyError, TypeError) as error:
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
