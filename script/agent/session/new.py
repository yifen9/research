from __future__ import annotations

from pathlib import Path
import sys

from research.agent.session import make_session
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
    if len(argv) != 4:
        raise ValueError("usage: new.py ROOT ROLE TOPIC")

    root = Path(argv[1]).resolve()
    role = argv[2]
    topic = argv[3]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "topic": topic},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        name, output = make_session(root, role, topic, run.run_dir)
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "topic": topic,
                "name": name,
                "output": [str(path) for path in output],
            },
        )

    except (ValueError, FileExistsError, KeyError, TypeError) as error:
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
