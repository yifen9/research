from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.json import read_json
from research.io.text import read_text, write_text
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress
from research.util.run import Run, make_run, run_err, run_ok, task_name
from research.util.versioner import recent_run


def read_audit(path: Path) -> dict[str, Any]:
    data = read_json(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def run_item(folder: str, meta: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(folder)
    audit_path = run_dir / "_audit.json"
    summary_path = run_dir / "_summary.md"

    if not audit_path.is_file():
        raise FileNotFoundError(str(audit_path))

    if not summary_path.is_file():
        raise FileNotFoundError(str(summary_path))

    audit = read_audit(audit_path)
    params = meta["params"]

    if not isinstance(params, dict):
        raise TypeError(str(run_dir / "_meta.json"))

    return {
        "run": str(run_dir),
        "task": params["task"],
        "status": audit["status"],
        "timestamp": meta["timestamp"],
        "fingerprint": meta["fingerprint"],
        "summary": str(summary_path),
    }


def load_run(run_dir: Path, limit: int, logger: Logger) -> list[dict[str, Any]]:
    data = recent_run(str(run_dir), limit)
    output: list[dict[str, Any]] = []
    progress = make_progress(logger, "run", len(data))

    progress.start()

    for folder, meta in data:
        item = run_item(folder, meta)
        output.append(item)
        logger.info(
            jline(
                "context",
                "run",
                "read",
                {
                    "run": item["run"],
                    "task": item["task"],
                    "status": item["status"],
                },
            )
        )
        progress.step(1)

    progress.finish()
    return output


def make_index(run_dir: Path, target: Path, limit: int) -> str:
    body: list[str] = []

    body.append("# Run Context\n")
    body.append("## Purpose\n")
    body.append("This directory summarizes recent execution state for agents.\n")
    body.append("## File\n")
    body.append("- [Latest](./latest.md)")
    body.append("- [Recent](./recent.md)")
    body.append("\n## Source\n")
    body.append(f"- run_dir: {run_dir}")
    body.append(f"- target: {target}")
    body.append(f"- limit: {limit}")
    body.append("\n## Rule\n")
    body.append("- Read latest.md first.")
    body.append("- Use recent.md only when recent history matters.")
    body.append("- Full audit artifacts remain under out/run.")
    body.append("")

    return "\n".join(body)


def make_recent(data: list[dict[str, Any]]) -> str:
    body: list[str] = []

    body.append("# Recent Run\n")
    body.append("| Time | Task | Status | Fingerprint | Summary |")
    body.append("|---|---|---|---|---|")

    for item in reversed(data):
        body.append(
            f"| {item['timestamp']} | {item['task']} | {item['status']} | {item['fingerprint']} | [{item['run']}](../../{item['summary']}) |"
        )

    body.append("")
    return "\n".join(body)


def make_latest(data: list[dict[str, Any]]) -> str:
    if not data:
        raise RuntimeError("no run found")

    item = data[-1]
    text = read_text(Path(item["summary"]))
    body: list[str] = []

    body.append("# Latest Run\n")
    body.append("## Index\n")
    body.append(f"- run: {item['run']}")
    body.append(f"- task: {item['task']}")
    body.append(f"- status: {item['status']}")
    body.append(f"- timestamp: {item['timestamp']}")
    body.append(f"- fingerprint: {item['fingerprint']}")
    body.append(f"- summary: {item['summary']}")
    body.append("\n---\n")
    body.append(text)

    return "\n".join(body)


def write_context(
    target: Path, run_dir: Path, limit: int, data: list[dict[str, Any]]
) -> list[Path]:
    output: list[Path] = []

    output.append(write_text(target / "index.md", make_index(run_dir, target, limit)))
    output.append(write_text(target / "recent.md", make_recent(data)))
    output.append(write_text(target / "latest.md", make_latest(data)))

    return output


def write_run(
    root: Path, run_dir: Path, target: Path, limit: int, logger: Logger
) -> list[Path]:
    data = load_run(run_dir, limit, logger)
    output = write_context(target, run_dir, limit, data)

    for path in output:
        logger.info(jline("context", "run", "write", {"path": str(path)}))

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
    if len(argv) != 5:
        raise ValueError("usage: write.py ROOT RUN_DIR TARGET LIMIT")

    root = Path(argv[1]).resolve()
    run_dir = Path(argv[2])
    target = Path(argv[3])
    limit = int(argv[4])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "run_dir": str(run_dir),
            "target": str(target),
            "limit": limit,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "run",
                "start",
                {
                    "root": str(root),
                    "run_dir": str(run_dir),
                    "target": str(target),
                    "limit": limit,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_run(root, run_dir, target, limit, run.logger)

        run.logger.info(
            jline(
                "script",
                "run",
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
                "run_dir": str(run_dir),
                "target": str(target),
                "limit": limit,
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
        fail(run, "run", error)


if __name__ == "__main__":
    main(sys.argv)
