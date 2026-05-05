from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from research.io.text import read_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def slug_ok(slug: str) -> None:
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) is None:
        raise ValueError("bad slug")


def project_path(root: Path, slug: str) -> Path:
    return root / "project" / slug


def proposal_path(root: Path, slug: str) -> Path:
    return project_path(root, slug) / "proposal"


def read_map(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def has_text(path: Path) -> bool:
    if not path.is_file():
        return False

    return bool(read_text(path).strip())


def git_status(root: Path, slug: str) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", f"project/{slug}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError((result.stdout + result.stderr).strip())

    return result.stdout.strip()


def check_proposal(root: Path, slug: str) -> list[dict[str, Any]]:
    slug_ok(slug)
    folder = project_path(root, slug)
    proposal = proposal_path(root, slug)
    bad: list[dict[str, Any]] = []

    for path in [folder / "meta.yaml", proposal / "meta.yaml", proposal / "main.tex"]:
        if not has_text(path):
            bad.append({"path": str(path), "kind": "missing"})

    if bad:
        return bad

    project = read_map(folder / "meta.yaml")
    data = read_map(proposal / "meta.yaml")

    if project.get("slug") != slug:
        bad.append({"path": str(folder / "meta.yaml"), "kind": "slug"})

    if data.get("project") != slug:
        bad.append({"path": str(proposal / "meta.yaml"), "kind": "project"})

    state = project.get("state")
    if state not in {"proposal", "active", "archive"}:
        bad.append({"path": str(folder / "meta.yaml"), "kind": "state"})

    if state == "active" and not has_text(proposal / "decision.yaml"):
        bad.append({"path": str(proposal / "decision.yaml"), "kind": "decision"})

    if state == "active" and git_status(root, slug):
        bad.append({"path": str(folder), "kind": "git"})

    return bad


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
    if len(argv) != 3:
        raise ValueError("usage: check.py ROOT SLUG")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        bad = check_proposal(root, slug)

        for item in bad:
            run.logger.error(jline("project", "proposal", "bad", item))

        if bad:
            raise RuntimeError("proposal check failed")

        run_ok(run, {"task": task, "slug": slug, "bad_count": 0})

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "proposal", error)


if __name__ == "__main__":
    main(sys.argv)
