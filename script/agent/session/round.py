from __future__ import annotations

from pathlib import Path
import sys

from research.agent.session import record_round
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
    if len(argv) != 7:
        raise ValueError("usage: round.py ROOT ROLE SESSION BACKEND USER_TEXT AI_TEXT")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    backend = argv[4]
    user_text = argv[5]
    ai_text = argv[6]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "name": name, "backend": backend},
        script=script,
        src=root / "src",
        config=root / "config" / "agent.yaml",
    )

    try:
        output = record_round(root, role, name, backend, user_text, ai_text, task, run.run_dir)
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "name": name,
                "backend": backend,
                "output": [str(path) for path in output],
            },
        )
    except (ValueError, FileNotFoundError, OSError, KeyError, TypeError) as error:
        fail(run, "session-round", error)


if __name__ == "__main__":
    main(sys.argv)
