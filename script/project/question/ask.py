from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
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


def git_call(root: Path, arg: list[str]) -> str:
    result = subprocess.run(
        ["git", *arg],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(output)

    return output


def branch_text(root: Path) -> str:
    return git_call(root, ["branch", "--show-current"])


def base_text(root: Path) -> str:
    return git_call(root, ["rev-parse", "HEAD"])


def project_ok(root: Path, slug: str) -> None:
    data = read_map(root / "project" / slug / "meta.yaml")

    if data.get("slug") != slug:
        raise ValueError("project slug mismatch")


def role_ask(role: str, target: str) -> None:
    role_ok(role)
    role_ok(target)

    if ROLE[target] <= ROLE[role]:
        raise ValueError("target role is not higher")


def question_path(root: Path, slug: str, name: str) -> Path:
    return root / "project" / slug / "question" / name / "meta.yaml"


def question_data(
    root: Path,
    slug: str,
    name: str,
    role: str,
    target_role: str,
    target: str,
    text: str,
    run: Run,
) -> dict[str, Any]:
    time = now_text()
    return {
        "id": name,
        "project": slug,
        "kind": "question",
        "state": "open",
        "role": role,
        "target_role": target_role,
        "target": target,
        "question": text,
        "run": run.run_dir,
        "branch": branch_text(root),
        "base": base_text(root),
        "created": time,
        "updated": time,
    }


def ask_question(
    root: Path,
    slug: str,
    name: str,
    role: str,
    target_role: str,
    target: str,
    text: str,
    run: Run,
) -> Path:
    slug_ok(slug)
    slug_ok(name)
    role_ask(role, target_role)
    project_ok(root, slug)

    if not text.strip():
        raise ValueError("empty text")

    path = question_path(root, slug, name)

    if path.exists():
        raise FileExistsError(str(path))

    path.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        write_yaml(
            str(path),
            question_data(root, slug, name, role, target_role, target, text, run),
        )
    )


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
        raise ValueError("usage: ask.py ROOT SLUG ID ROLE TARGET_ROLE TARGET TEXT")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    name = argv[3]
    role = argv[4]
    target_role = argv[5]
    target = argv[6]
    text = " ".join(argv[7:])
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
        output = ask_question(root, slug, name, role, target_role, target, text, run)
        run_ok(run, {"task": task, "slug": slug, "id": name, "output": [str(output)]})

    except (
        ValueError,
        KeyError,
        FileExistsError,
        FileNotFoundError,
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "question", error)


if __name__ == "__main__":
    main(sys.argv)
