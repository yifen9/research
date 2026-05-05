from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

from research.io.jsonl import append_jsonl
from research.io.text import write_text
from research.io.yaml import write_yaml
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

    if (
        role != "architect"
        and (root / "out" / "agent" / "memory" / f"{role}.md").is_file()
    ):
        body.append(f"- out/agent/memory/{role}.md")

    if (
        role != "architect"
        and (root / "out" / "agent" / "handoff" / f"{role}.md").is_file()
    ):
        body.append(f"- out/agent/handoff/{role}.md")

    body.append("")
    return "\n".join(body)


def event_data(role: str, name: str, run: Run) -> dict[str, Any]:
    return {
        "time": now_text(),
        "actor": role,
        "role": role,
        "event": "session-new",
        "target": name,
        "run": run.run_dir,
    }


def write_event(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(str(path), data)
    return path


def write_session(root: Path, role: str, topic: str, run: Run) -> list[Path]:
    role_ok(role)
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
    if len(argv) != 4:
        raise ValueError("usage: new.py ROOT ROLE TOPIC")

    root = Path(argv[1]).resolve()
    role = argv[2]
    topic = argv[3]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "role": role, "topic": topic},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = write_session(root, role, topic, run)
        run_ok(
            run,
            {
                "task": task,
                "role": role,
                "topic": topic,
                "output": [str(path) for path in output],
            },
        )

    except (ValueError, FileExistsError, TypeError) as error:
        fail(run, "session", error)


if __name__ == "__main__":
    main(sys.argv)
