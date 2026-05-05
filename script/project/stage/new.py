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


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug_ok(slug: str) -> None:
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) is None:
        raise ValueError("bad slug")


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

    if data.get("state") not in {"active", "stage", "result", "publish"}:
        raise ValueError("project is not active")


def stage_path(root: Path, slug: str, stage: str) -> Path:
    return root / "project" / slug / "stage" / stage / "meta.yaml"


def stage_data(
    root: Path, slug: str, stage: str, title: str, run: Run
) -> dict[str, Any]:
    time = now_text()
    return {
        "id": f"{slug}-{stage}",
        "project": slug,
        "stage": stage,
        "kind": "stage",
        "state": "active",
        "title": title,
        "role": "manager",
        "run": run.run_dir,
        "branch": branch_text(root),
        "base": base_text(root),
        "target": f"project/{slug}/stage/{stage}",
        "created": time,
        "updated": time,
    }


def write_stage(root: Path, slug: str, stage: str, title: str, run: Run) -> Path:
    slug_ok(slug)
    slug_ok(stage)
    project_ok(root, slug)

    if not title.strip():
        raise ValueError("empty title")

    path = stage_path(root, slug, stage)

    if path.exists():
        raise FileExistsError(str(path))

    path.parent.mkdir(parents=True, exist_ok=True)
    return Path(write_yaml(str(path), stage_data(root, slug, stage, title, run)))


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
        raise ValueError("usage: new.py ROOT SLUG STAGE TITLE")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    stage = argv[3]
    title = " ".join(argv[4:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug, "stage": stage, "title": title},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = write_stage(root, slug, stage, title, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "stage": stage,
                "output": [str(output)],
            },
        )

    except (
        ValueError,
        KeyError,
        FileExistsError,
        FileNotFoundError,
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "stage", error)


if __name__ == "__main__":
    main(sys.argv)
