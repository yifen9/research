from __future__ import annotations

from pathlib import Path
import sys

from research.util.data import write_meta
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
    if len(argv) != 3:
        raise ValueError("usage: add.py ROOT BASE")

    root = Path(argv[1]).resolve()
    base = Path(argv[2]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "base": str(base)},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        path = write_meta(base, run.meta["timestamp"])
        run_ok(run, {"task": task, "base": str(base), "path": str(path)})

    except (ValueError, KeyError, FileNotFoundError, TypeError) as error:
        fail(run, "data", error)


if __name__ == "__main__":
    main(sys.argv)
