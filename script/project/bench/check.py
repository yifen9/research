from __future__ import annotations

from pathlib import Path
import sys

from research.io.yaml import read_yaml
from research.util.bench import check_bench
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
    if len(argv) != 5:
        raise ValueError("usage: check.py ROOT SLUG EXPERIMENT METRIC")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    experiment = argv[3]
    path = Path(argv[4]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "slug": slug,
            "experiment": experiment,
            "metric": str(path),
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        meta = read_yaml(
            str(root / "project" / slug / "experiment" / experiment / "meta.yaml")
        )
        metric = read_yaml(str(path))
        bench: list = []

        if "bench" in meta:
            bench = meta["bench"]

        summary = check_bench(bench, metric)

        if summary["status"] != "pass":
            error = RuntimeError("bench failed")
            run_err(run, error, {"task": task, "summary": summary})
            sys.exit(1)

        run_ok(run, {"task": task, "summary": summary})

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "bench", error)


if __name__ == "__main__":
    main(sys.argv)
