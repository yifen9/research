from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

from research.io.jsonl import append_jsonl
from research.io.text import read_text, write_text
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


def handoff_path(root: Path, role: str) -> Path:
    return root / "out" / "agent" / "handoff" / f"{role}.md"


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def ensure_text(path: Path) -> str:
    text = read_text(path).strip()

    if not text:
        raise ValueError(str(path))

    return text + "\n"


def event_data(role: str, name: str, run: Run) -> dict[str, Any]:
    return {
        "time": now_text(),
        "actor": role,
        "role": role,
        "event": "handoff-write",
        "target": name,
        "run": run.run_dir,
    }


def write_event(path: Path, data: dict[str, Any]) -> Path:
    append_jsonl(str(path), data)
    return path


def write_handoff(
    root: Path, role: str, name: str, handoff: Path, run: Run
) -> list[Path]:
    role_ok(role)
    folder = session_path(root, role, name)
    data = read_map(folder / "session.yaml")

    if data["state"] != "active":
        raise ValueError("session is not active")

    text = ensure_text(handoff)
    output: list[Path] = []
    output.append(write_text(folder / "handoff.md", text))
    output.append(write_text(handoff_path(root, role), text))
    data["handoff"] = "handoff.md"
    data["role_handoff"] = str(handoff_path(root, role).relative_to(root))
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
    if len(argv) != 5:
        raise ValueError("usage: write.py ROOT ROLE ID HANDOFF")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    handoff = Path(argv[4])
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
        output = write_handoff(root, role, name, handoff, run)
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
        fail(run, "handoff", error)


if __name__ == "__main__":
    main(sys.argv)
