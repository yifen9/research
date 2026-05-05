from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
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


def topic_text(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    if not slug:
        raise ValueError("empty topic")

    return slug


def role_ok(role: str) -> None:
    if role not in ROLE:
        raise ValueError("unknown role")


def make_id(time: str, topic: str) -> str:
    date = datetime.fromisoformat(time).strftime("%Y%m%dT%H%M%S")
    return f"{date}-{topic}"


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


def event_data(role: str, name: str, event: str, run: Run) -> dict[str, Any]:
    return {
        "time": now_text(),
        "actor": role,
        "role": role,
        "event": event,
        "target": name,
        "run": run.run_dir,
    }


def write_event(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(str(path), data)
    return path


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


def initial_text(root: Path, role: str) -> str:
    body: list[str] = []
    body.append("# Initial Context\n")
    body.append("## Common\n")
    body.append("- agent/agent.md")
    body.append("- agent/context/index.md")
    body.append("- agent/context/rule/_manifest.md")
    body.append(f"- agent/workflow/role/{role}.md")
    body.append(f"- agent/workflow/session/{role}.md")

    if role == "architect":
        body.append("- agent/context/project/overview.md")
        body.append("- agent/context/profile/user/research.md")
        body.append("- agent/context/profile/user/projects.md")
        body.append("- agent/context/run/latest.md")
        body.append("- out/agent/memory/architect.md")
        body.append("- out/agent/handoff/architect.md")

    if role != "architect" and memory_path(root, role).is_file():
        body.append(f"- out/agent/memory/{role}.md")

    if role != "architect" and handoff_path(root, role).is_file():
        body.append(f"- out/agent/handoff/{role}.md")

    body.append("")
    return "\n".join(body)


def close_data(role: str, name: str, run: Run) -> dict[str, Any]:
    return {
        "id": name,
        "role": role,
        "state": "closed",
        "closed": now_text(),
        "run": run.run_dir,
    }


def close_session(
    root: Path,
    role: str,
    name: str,
    memory: Path,
    summary: Path,
    handoff: Path,
    run: Run,
) -> list[Path]:
    folder = session_path(root, role, name)
    data = read_map(folder / "session.yaml")

    if data["state"] != "active":
        raise ValueError("session is not active")

    memory_body = ensure_text(memory)
    summary_body = ensure_text(summary)
    handoff_body = ensure_text(handoff)
    close = close_data(role, name, run)
    output: list[Path] = []
    output.append(write_text(folder / "memory.md", memory_body))
    output.append(write_text(folder / "summary.md", summary_body))
    output.append(write_text(folder / "handoff.md", handoff_body))
    output.append(
        write_text(memory_path(root, role), memory_text(role, name, memory_body, summary_body, run))
    )
    output.append(write_text(handoff_path(root, role), handoff_body))
    output.append(Path(write_yaml(str(folder / "close.yaml"), close)))
    data["state"] = "closed"
    data["closed"] = close["closed"]
    data["handoff"] = "handoff.md"
    data["role_memory"] = str(memory_path(root, role).relative_to(root))
    data["role_handoff"] = str(handoff_path(root, role).relative_to(root))
    output.append(Path(write_yaml(str(folder / "session.yaml"), data)))
    output.append(write_event(folder / "event.jsonl", event_data(role, name, "session-close", run)))
    return output


def write_session(root: Path, role: str, topic: str, run: Run) -> tuple[str, list[Path]]:
    topic = topic_text(topic)
    time = now_text()
    name = make_id(time, topic)
    folder = session_path(root, role, name)

    if folder.exists():
        raise FileExistsError(str(folder))

    folder.mkdir(parents=True, exist_ok=False)
    data = {
        "id": name,
        "role": role,
        "state": "active",
        "topic": topic,
        "started": time,
        "closed": None,
        "initial": "initial.md",
        "memory": "memory.md",
        "summary": "summary.md",
        "run": run.run_dir,
    }
    output: list[Path] = []
    output.append(Path(write_yaml(str(folder / "session.yaml"), data)))
    output.append(write_text(folder / "initial.md", initial_text(root, role)))
    output.append(write_text(folder / "message.jsonl", ""))
    output.append(write_text(folder / "event.jsonl", ""))
    output.append(write_event(folder / "event.jsonl", event_data(role, name, "session-new", run)))
    return name, output


def rotate_session(
    root: Path,
    role: str,
    name: str,
    memory: Path,
    summary: Path,
    handoff: Path,
    topic: str,
    run: Run,
) -> dict[str, Any]:
    role_ok(role)
    output = close_session(root, role, name, memory, summary, handoff, run)
    target, data = write_session(root, role, topic, run)
    output.extend(data)
    return {
        "closed": name,
        "opened": target,
        "output": [str(path) for path in output],
    }


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
    if len(argv) < 8:
        raise ValueError("usage: rotate.py ROOT ROLE ID MEMORY SUMMARY HANDOFF TOPIC")

    root = Path(argv[1]).resolve()
    role = argv[2]
    name = argv[3]
    memory = Path(argv[4])
    summary = Path(argv[5])
    handoff = Path(argv[6])
    topic = " ".join(argv[7:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "id": name, "topic": topic},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        data = rotate_session(root, role, name, memory, summary, handoff, topic, run)
        run_ok(run, {"task": task, "role": role, **data})

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
