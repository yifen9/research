from __future__ import annotations

from pathlib import Path
import sys

from research.util.jlog import jline
from research.util.repo import repo_push
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
    if len(argv) != 5:
        raise ValueError("usage: push.py ROOT DIR USER NAME")

    root = Path(argv[1]).resolve()
    target = Path(argv[2]).resolve()
    user = argv[3]
    name = argv[4]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "target": str(target),
            "user": user,
            "name": name,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = repo_push(target, user, name)
        run_ok(run, {"task": task, "name": name, "output": output})

    except (ValueError, RuntimeError, TypeError) as error:
        fail(run, "repo", error)


if __name__ == "__main__":
    main(sys.argv)
