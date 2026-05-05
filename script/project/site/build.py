from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def project_block(slug: Path) -> list[str]:
    meta_file = slug / "meta.yaml"

    if not meta_file.is_file():
        return []

    data: dict[str, Any] = read_yaml(str(meta_file))
    body: list[str] = []
    body.append(f"## {data['title']}")
    body.append("")

    if "description" in data:
        body.append(data["description"])
        body.append("")

    if "state" in data:
        body.append(f"- state: {data['state']}")

    if "repo" in data and isinstance(data["repo"], list):
        for item in data["repo"]:
            body.append(f"- repo: {item}")

    body.append("")
    return body


def build_site(root: Path) -> Path:
    base = root / "project"
    body: list[str] = []
    body.append("---")
    body.append("title: Projects")
    body.append("---")
    body.append("")
    body.append("# Projects")
    body.append("")

    if base.is_dir():
        for slug in sorted(base.iterdir()):
            if slug.is_dir():
                body.extend(project_block(slug))

    return write_text(root / "project" / "index.qmd", "\n".join(body))


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
    if len(argv) != 2:
        raise ValueError("usage: build.py ROOT")

    root = Path(argv[1]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        path = build_site(root)
        run_ok(run, {"task": task, "path": str(path)})

    except (ValueError, KeyError, FileNotFoundError, TypeError) as error:
        fail(run, "site", error)


if __name__ == "__main__":
    main(sys.argv)
