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


def memory_path(root: Path, role: str) -> Path:
    return root / "out" / "agent" / "memory" / f"{role}.md"


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
        "event": "session-close",
        "target": name,
        "run": run.run_dir,
    }


def write_event(path: Path, data: dict[str, Any]) -> Path:
    append_jsonl(str(path), data)
    return path


def close_data(role: str, name: str, run: Run) -> dict[str, Any]:
    return {
        "id": name,
        "role": role,
        "state": "closed",
        "closed": now_text(),
        "run": run.run_dir,
    }


def memory_text(role: str, name: str, memory: str, summary: str, run: Run) -> str:
    body: list[str] = []
    body.append(f"# {role.title()} Memory\n")
    body.append("## Session\n")
    body.append(f"- id: {name}")
    body.append(f"- run: {run.run_dir}")
    body.append(f"- updated: {now_text()}")
    body.append("\n## Memory\n")
    body.append(memory.strip())
    body.append("\n## Summary\n")
    body.append(summary.strip())
    body.append("")
    return "\n".join(body)


def write_memory(
    root: Path,
    role: str,
    name: str,
    memory: str,
    summary: str,
    run: Run,
) -> Path:
    return write_text(
        memory_path(root, role), memory_text(role, name, memory, summary, run)
    )


def sync_handoff(root: Path, role: str, folder: Path) -> Path | None:
    source = folder / "handoff.md"

    if not source.is_file():
        return None

    return write_text(handoff_path(root, role), ensure_text(source))


def close_session(
    root: Path, role: str, name: str, memory: Path, summary: Path, run: Run
) -> list[Path]:
    role_ok(role)
    folder = session_path(root, role, name)
    data = read_map(folder / "session.yaml")

    if data["state"] != "active":
        raise ValueError("session is not active")

    output: list[Path] = []
    memory_body = ensure_text(memory)
    summary_body = ensure_text(summary)
    output.append(write_text(folder / "memory.md", memory_body))
    output.append(write_text(folder / "summary.md", summary_body))
    output.append(write_memory(root, role, name, memory_body, summary_body, run))

    close = close_data(role, name, run)
    output.append(Path(write_yaml(str(folder / "close.yaml"), close)))

    data["state"] = "closed"
    data["closed"] = close["closed"]
    data["role_memory"] = str(memory_path(root, role).relative_to(root))
    handoff = sync_handoff(root, role, folder)

    if handoff is not None:
        data["role_handoff"] = str(handoff.relative_to(root))

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
    if len(argv) != 6:
        raise ValueError("usage: close.py ROOT ROLE ID MEMORY SUMMARY")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    memory = Path(argv[4])
    summary = Path(argv[5])
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
        output = close_session(root, role, name, memory, summary, run)
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
