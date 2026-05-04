from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def read_data(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def write_data(path: Path, data: dict[str, Any]) -> Path:
    return write_text(path, yaml_text(data))


def summary_text(data: dict[str, Any]) -> str:
    body: list[str] = []

    body.append("# Session Summary\n")
    body.append("## Status\n")
    body.append(f"- session: {data['session']}")
    body.append(f"- role: {data['role']}")
    body.append(f"- status: {data['status']}")
    body.append(f"- threshold: {data['threshold']}")
    body.append(f"- task_count: {data['task_count']}")
    body.append(f"- accept_count: {data['accept_count']}")
    body.append(f"- reject_count: {data['reject_count']}")
    body.append(f"- pass_rate: {data['pass_rate']}")
    body.append(f"- created_run: {data['created_run']}")

    if "retire_run" in data:
        body.append(f"- retire_run: {data['retire_run']}")

    if "retire_reason" in data:
        body.append(f"- retire_reason: {data['retire_reason']}")

    body.append("\n## File\n")
    body.append("- state: state.yaml")
    body.append("- memory: memory.md")
    body.append("")

    return "\n".join(body)


def memory_text(data: dict[str, Any], reason: str) -> str:
    body: list[str] = []

    body.append("# Session Memory\n")
    body.append("## Session\n")
    body.append(f"- session: {data['session']}")
    body.append(f"- role: {data['role']}")
    body.append(f"- status: {data['status']}")
    body.append(f"- reason: {reason}")
    body.append("\n## Metric\n")
    body.append(f"- task_count: {data['task_count']}")
    body.append(f"- accept_count: {data['accept_count']}")
    body.append(f"- reject_count: {data['reject_count']}")
    body.append(f"- pass_rate: {data['pass_rate']}")
    body.append("\n## Common Failure\n")
    body.append("To be filled before reuse.")
    body.append("\n## Useful Knowledge\n")
    body.append("To be filled before reuse.")
    body.append("\n## Next Session Advice\n")
    body.append("To be filled before reuse.")
    body.append("")

    return "\n".join(body)


def retire_session(
    session_dir: Path,
    session: str,
    reason: str,
    run_dir: str,
) -> dict[str, Any]:
    path = session_dir / session
    state_path = path / "state.yaml"

    if not state_path.is_file():
        raise FileNotFoundError(str(state_path))

    data = read_data(state_path)

    if data["status"] == "retired":
        raise ValueError("session already retired")

    data["status"] = "retired"
    data["retire_reason"] = reason
    data["retire_run"] = run_dir

    write_data(state_path, data)
    write_text(path / "_summary.md", summary_text(data))
    write_text(path / "memory.md", memory_text(data, reason))

    return data


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
        raise ValueError("usage: retire.py ROOT SESSION_DIR SESSION REASON")

    root = Path(argv[1]).resolve()
    session_dir = Path(argv[2])
    session = argv[3]
    reason = argv[4]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "session_dir": str(session_dir),
            "session": session,
            "reason": reason,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "retire",
                "start",
                {
                    "root": str(root),
                    "session_dir": str(session_dir),
                    "session": session,
                    "reason": reason,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = retire_session(session_dir, session, reason, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "retire",
                "ok",
                {
                    "session": session,
                    "role": data["role"],
                    "status": data["status"],
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "session": session,
                "role": data["role"],
                "status": data["status"],
                "reason": reason,
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
        fail(run, "retire", error)


if __name__ == "__main__":
    main(sys.argv)
