from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

from research.io.yaml import read_yaml, write_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


ROLE = {"architect": 3, "manager": 2, "reviewer": 1, "worker": 0}


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug_ok(slug: str) -> None:
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) is None:
        raise ValueError("bad slug")


def role_ok(role: str) -> None:
    if role not in ROLE:
        raise ValueError("unknown role")


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def question_path(root: Path, slug: str, name: str) -> Path:
    return root / "project" / slug / "question" / name / "meta.yaml"


def role_answer(role: str, target: str) -> None:
    role_ok(role)
    role_ok(target)

    if ROLE[role] < ROLE[target]:
        raise ValueError("role cannot answer")


def answer_question(
    root: Path, slug: str, name: str, role: str, text: str, run: Run
) -> Path:
    slug_ok(slug)
    slug_ok(name)
    path = question_path(root, slug, name)
    data = read_map(path)
    target_role = str(data["target_role"])
    role_answer(role, target_role)

    if data.get("state") != "open":
        raise ValueError("question is not open")

    if not text.strip():
        raise ValueError("empty text")

    time = now_text()
    data["state"] = "answered"
    data["answer"] = text
    data["answer_role"] = role
    data["answer_run"] = run.run_dir
    data["answered"] = time
    data["updated"] = time
    return Path(write_yaml(str(path), data))


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
    if len(argv) < 6:
        raise ValueError("usage: answer.py ROOT SLUG ID ROLE TEXT")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    name = argv[3]
    role = argv[4]
    text = " ".join(argv[5:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug, "id": name},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = answer_question(root, slug, name, role, text, run)
        run_ok(run, {"task": task, "slug": slug, "id": name, "output": [str(output)]})

    except (ValueError, KeyError, FileNotFoundError, TypeError) as error:
        fail(run, "question", error)


if __name__ == "__main__":
    main(sys.argv)
