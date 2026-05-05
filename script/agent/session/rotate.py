from __future__ import annotations

from pathlib import Path
import sys

from research.agent.session import rotate_session
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
    if len(argv) != 8:
        raise ValueError("usage: rotate.py ROOT ROLE ID MEMORY SUMMARY HANDOFF TOPIC")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    memory = Path(argv[4]).resolve()
    summary = Path(argv[5]).resolve()
    handoff = Path(argv[6]).resolve()
    topic = argv[7]
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
            "handoff": str(handoff),
            "topic": topic,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        new_name, output = rotate_session(
            root,
            role,
            name,
            read_text(memory),
            read_text(summary),
            read_text(handoff),
            topic,
            run.run_dir,
        )
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "name": name,
                "new_name": new_name,
                "topic": topic,
                "output": [str(path) for path in output],
            },
        )

    except (ValueError, FileNotFoundError, FileExistsError, KeyError, TypeError) as error:
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
