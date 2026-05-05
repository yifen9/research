from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

from research.io.jsonl import append_jsonl
from research.io.yaml import read_yaml, write_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


ROLE = {"architect", "manager", "reviewer", "worker"}


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def role_ok(role: str) -> None:
    if role not in ROLE:
        raise ValueError("unknown role")


def session_path(root: Path, role: str, name: str) -> Path:
    return root / "out" / "agent" / "session" / role / name


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def retire_data(role: str, name: str, text: str, run: Run) -> dict[str, Any]:
    return {
        "id": name,
        "role": role,
        "state": "retired",
        "reason": text,
        "retired": now_text(),
        "run": run.run_dir,
    }


def event_data(role: str, name: str, run: Run) -> dict[str, Any]:
    return {
        "time": now_text(),
        "actor": role,
        "role": role,
        "event": "session-retire",
        "target": name,
        "run": run.run_dir,
    }


def write_event(path: Path, data: dict[str, Any]) -> Path:
    append_jsonl(str(path), data)
    return path


def retire_session(root: Path, role: str, name: str, text: str, run: Run) -> list[Path]:
    role_ok(role)
    folder = session_path(root, role, name)
    data = read_map(folder / "session.yaml")

    if data["state"] == "retired":
        raise ValueError("session is retired")

    if not text.strip():
        raise ValueError("empty text")

    retire = retire_data(role, name, text, run)
    data["state"] = "retired"
    data["retired"] = retire["retired"]
    data["retire"] = "retire.yaml"
    output: list[Path] = []
    output.append(Path(write_yaml(str(folder / "retire.yaml"), retire)))
    output.append(Path(write_yaml(str(folder / "session.yaml"), data)))
    output.append(write_event(folder / "event.jsonl", event_data(role, name, run)))
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
    if len(argv) < 5:
        raise ValueError("usage: retire.py ROOT ROLE ID TEXT")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    text = " ".join(argv[4:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "id": name},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = retire_session(root, role, name, text, run)
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "id": name,
                "output": [str(path) for path in output],
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        TypeError,
    ) as error:
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
