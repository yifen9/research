from __future__ import annotations

import json
from pathlib import Path
import sys

from research.agent.session import record_active
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def read_data(data: bytes, max_byte: int) -> dict[str, object]:
    if len(data) > max_byte:
        raise ValueError("payload too large")

    item = json.loads(data.decode("utf-8"))
    if not isinstance(item, dict):
        raise TypeError("payload")
    return item


def read_input(max_byte: int) -> dict[str, object]:
    return read_data(sys.stdin.buffer.read(max_byte + 1), max_byte)


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
        raise ValueError("usage: auto_round.py ROOT ROLE SOURCE MAX_BYTES")

    root = Path(argv[1]).resolve()
    role = argv[2]
    source = argv[3]
    max_byte = int(argv[4])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "source": source, "max": max_byte},
        script=script,
        src=root / "src",
        config=root / "config" / "agent.yaml",
    )

    try:
        data = read_input(max_byte)
        user_text = str(data["user_text"])
        ai_text = str(data["ai_text"])
        output = record_active(root, role, user_text, ai_text, source, run.run_dir)
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "source": source,
                "output": [str(path) for path in output],
            },
        )
    except (json.JSONDecodeError, ValueError, FileNotFoundError, OSError, KeyError, TypeError) as error:
        fail(run, "session-auto-round", error)


if __name__ == "__main__":
    main(sys.argv)
