from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.agent.provider import Req, make_provider
from research.io.text import read_text, write_text
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


def agent_data(path: Path) -> dict[str, Any]:
    data = read_data(path)

    if "agent" not in data:
        raise KeyError("agent")

    item = data["agent"]

    if not isinstance(item, dict):
        raise TypeError("agent")

    return item


def result_data(change_dir: Path, change: str) -> dict[str, Any]:
    path = change_dir / change / "result.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return read_data(path)


def task_path(change_dir: Path, change: str) -> Path:
    path = change_dir / change / "task.md"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path


def worker_id(change_dir: Path, change: str) -> str:
    data = result_data(change_dir, change)

    if "worker" in data and data["worker"] is not None:
        return str(data["worker"])

    text = read_text(task_path(change_dir, change))

    for line in text.splitlines():
        if line.startswith("- worker:"):
            return line.removeprefix("- worker:").strip()

    raise KeyError("worker")


def context_text(context_dir: Path) -> str:
    files = [
        context_dir / "index.md",
        context_dir / "run" / "latest.md",
        context_dir / "project" / "_manifest.md",
        context_dir / "rule" / "_manifest.md",
        context_dir / "workflow" / "artifact" / "task.md",
    ]

    body: list[str] = []

    for path in files:
        if not path.is_file():
            raise FileNotFoundError(str(path))

        body.append(f"# File: {path}")
        body.append(read_text(path))
        body.append("")

    return "\n".join(body)


def strip_fence(text: str) -> str:
    data = text.strip()

    if data.startswith("```markdown"):
        data = data.removeprefix("```markdown").strip()

    if data.startswith("```"):
        data = data.removeprefix("```").strip()

    if data.endswith("```"):
        data = data.removesuffix("```").strip()

    return data + "\n"


def prompt_text(context_dir: Path, change: str, worker: str, title: str) -> str:
    body: list[str] = []

    body.append("# Task Draft Request\n")
    body.append("Write a complete task.md for an agent worker.")
    body.append("Return Markdown only.")
    body.append("Do not include code fences.")
    body.append("Do not leave placeholders.")
    body.append("Do not write 'To be filled'.")
    body.append("The task must be concrete, executable, and reviewable.\n")
    body.append("The task must contain exactly these sections:\n")
    body.append("# Task")
    body.append("## Title")
    body.append("## Change")
    body.append("## Objective")
    body.append("## Scope")
    body.append("## Required Command")
    body.append("## Expected Output\n")
    body.append("The Change section must include exactly:")
    body.append(f"- id: {change}")
    body.append(f"- worker: {worker}\n")
    body.append("## Title Input\n")
    body.append(title)
    body.append("\n## Context\n")
    body.append(context_text(context_dir))

    return "\n".join(body)


def section_text(text: str, name: str) -> str:
    lines = text.splitlines()
    start = -1
    body: list[str] = []

    for idx, line in enumerate(lines):
        if line.strip() == f"## {name}":
            start = idx + 1
            break

    if start < 0:
        raise KeyError(name)

    for line in lines[start:]:
        if line.startswith("## "):
            break

        body.append(line)

    return "\n".join(body).strip()


def check_field(text: str, name: str) -> None:
    value = section_text(text, name)

    if not value:
        raise ValueError(f"empty field: {name}")

    if "To be filled" in value:
        raise ValueError(f"placeholder field: {name}")


def check_task(change_dir: Path, change: str) -> dict[str, Any]:
    path = task_path(change_dir, change)
    text = read_text(path)

    check_field(text, "Title")
    check_field(text, "Objective")
    check_field(text, "Scope")
    check_field(text, "Required Command")
    check_field(text, "Expected Output")

    data = {
        "change": change,
        "path": str(path),
        "status": "checked",
    }

    write_text(change_dir / change / "task.yaml", yaml_text(data))
    return data


def write_task(
    provider_path: Path,
    context_dir: Path,
    change_dir: Path,
    change: str,
) -> Path:
    provider = make_provider(read_data(provider_path))
    result = result_data(change_dir, change)
    worker = worker_id(change_dir, change)
    title = str(result["title"])
    text = prompt_text(context_dir, change, worker, title)

    resp = provider.send(
        Req(
            role="task",
            text=text,
            meta={
                "change": change,
                "title": title,
            },
        )
    )

    final = strip_fence(resp.text)
    path = task_path(change_dir, change)

    return write_text(path, final)


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
    if len(argv) != 7:
        raise ValueError(
            "usage: task.py ROOT AGENT_CONFIG PROVIDER_CONFIG CONTEXT_DIR CHANGE_DIR CHANGE"
        )

    root = Path(argv[1]).resolve()
    agent_path = Path(argv[2])
    provider_path = Path(argv[3])
    context_dir = Path(argv[4])
    change_dir = Path(argv[5])
    change = argv[6]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    agent_data(agent_path)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "agent_config": str(agent_path),
            "provider_config": str(provider_path),
            "context_dir": str(context_dir),
            "change_dir": str(change_dir),
            "change": change,
        },
        script=script,
        src=root / "src",
        config=agent_path,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "task",
                "start",
                {
                    "root": str(root),
                    "agent_config": str(agent_path),
                    "provider_config": str(provider_path),
                    "context_dir": str(context_dir),
                    "change_dir": str(change_dir),
                    "change": change,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        path = write_task(provider_path, context_dir, change_dir, change)
        data = check_task(change_dir, change)

        run.logger.info(
            jline(
                "script",
                "task",
                "ok",
                {
                    "path": str(path),
                    "status": data["status"],
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "change": change,
                "path": str(path),
                "status": data["status"],
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
        NotImplementedError,
    ) as error:
        fail(run, "task", error)


if __name__ == "__main__":
    main(sys.argv)
