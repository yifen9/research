from __future__ import annotations

from pathlib import Path
import sys

from research.agent.check import check_backend
from research.agent.config import backend_name, read_config
from research.agent.load import load_backend
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
    if len(argv) != 2:
        raise ValueError("usage: check.py ROOT")

    root = Path(argv[1]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)
    config = root / "config" / "agent.yaml"

    run = make_run(
        root=root,
        name=task,
        params={"task": task},
        script=script,
        src=root / "src",
        config=config,
    )

    try:
        name = backend_name(read_config(root))
        bad = check_backend(load_backend(root, name))

        if bad:
            error = RuntimeError("backend check failed")
            run_err(run, error, {"task": task, "name": name, "bad": bad})
            sys.exit(1)

        run_ok(run, {"task": task, "name": name, "bad": []})

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "backend", error)


if __name__ == "__main__":
    main(sys.argv)
