from __future__ import annotations

from pathlib import Path
import sys

from research.agent.audit import message_record
from research.agent.session import record_message
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
        raise ValueError("usage: message.py ROOT ROLE SESSION ACTOR KIND TEXT")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    actor = argv[4]
    kind = argv[5]
    text = argv[6]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "name": name, "actor": actor, "kind": kind},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        path = record_message(root, role, name, message_record(actor, text, kind, run.run_dir))
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "name": name,
                "actor": actor,
                "kind": kind,
                "output": str(path),
            },
        )
    except (ValueError, FileNotFoundError, OSError, KeyError, TypeError) as error:
        fail(run, "session-message", error)


if __name__ == "__main__":
    main(sys.argv)
