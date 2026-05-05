from __future__ import annotations

from pathlib import Path
import sys

from research.agent.handoff import write_handoff
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
    if len(argv) != 4:
        raise ValueError("usage: write.py ROOT ROLE TEXT")

    root = Path(argv[1]).resolve()
    role = argv[2]
    text = Path(argv[3]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "text": str(text)},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        path = write_handoff(root, role, read_text(text))
        run_ok(run, {"task": task, "role": role, "path": str(path)})

    except (ValueError, FileNotFoundError, KeyError, TypeError) as error:
        fail(run, "handoff", error)


if __name__ == "__main__":
    main(sys.argv)
