from __future__ import annotations

from pathlib import Path
import sys

from research.util.jlog import jline
from research.util.mirror import write_mirror
from research.util.run import Run, make_run, run_err, run_ok, task_name


def write_workflow(root: Path, source: Path, target: Path, run: Run) -> list[Path]:
    output = write_mirror(source, target, run.logger)

    for path in output:
        run.logger.info(jline("context", "workflow", "write", {"path": str(path)}))

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
        raise ValueError("usage: write.py ROOT SOURCE TARGET")

    root = Path(argv[1]).resolve()
    source = Path(argv[2])
    target = Path(argv[3])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "source": str(source),
            "target": str(target),
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "workflow",
                "start",
                {
                    "root": str(root),
                    "source": str(source),
                    "target": str(target),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_workflow(root, source, target, run)

        run.logger.info(
            jline(
                "script",
                "workflow",
                "ok",
                {
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
                "source": str(source),
                "target": str(target),
                "output": len(output),
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "workflow", error)


if __name__ == "__main__":
    main(sys.argv)
