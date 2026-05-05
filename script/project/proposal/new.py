from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

from research.io.text import read_text, write_text
from research.io.yaml import write_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


AUTHOR = "Li Yifeng"
EMAIL = "mail@yifen9.li"
SITE = "https://yifen9.li"


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug_ok(slug: str) -> None:
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) is None:
        raise ValueError("bad slug")


def project_path(root: Path, slug: str) -> Path:
    return root / "project" / slug


def proposal_path(root: Path, slug: str) -> Path:
    return project_path(root, slug) / "proposal"


def write_main(source: Path, target: Path, title: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    text = read_text(source).replace("Project Title", title)
    return write_text(target, text)


def project_data(slug: str, title: str, run: Run) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "state": "proposal",
        "created": now_text(),
        "proposal": "proposal/meta.yaml",
        "run": run.run_dir,
    }


def proposal_data(slug: str, title: str, run: Run) -> dict[str, Any]:
    return {
        "kind": "project-proposal",
        "project": slug,
        "state": "draft",
        "title": title,
        "author": AUTHOR,
        "email": EMAIL,
        "site": SITE,
        "created": now_text(),
        "run": run.run_dir,
    }


def write_proposal(root: Path, slug: str, title: str, run: Run) -> list[Path]:
    slug_ok(slug)
    folder = project_path(root, slug)

    if folder.exists():
        raise FileExistsError(str(folder))

    proposal = proposal_path(root, slug)
    template = root / "template" / "project" / "proposal"
    proposal.mkdir(parents=True, exist_ok=False)
    output: list[Path] = []
    output.append(
        Path(write_yaml(str(folder / "meta.yaml"), project_data(slug, title, run)))
    )
    output.append(
        Path(write_yaml(str(proposal / "meta.yaml"), proposal_data(slug, title, run)))
    )
    output.append(write_main(template / "main.tex", proposal / "main.tex", title))
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
    if len(argv) < 4:
        raise ValueError("usage: new.py ROOT SLUG TITLE")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    title = " ".join(argv[3:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug, "title": title},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = write_proposal(root, slug, title, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "title": title,
                "output": [str(path) for path in output],
            },
        )

    except (ValueError, FileExistsError, FileNotFoundError, TypeError) as error:
        fail(run, "proposal", error)


if __name__ == "__main__":
    main(sys.argv)
