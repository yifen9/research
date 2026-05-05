from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

from research.io.text import read_text
from research.io.yaml import read_yaml, write_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def ensure_text(text: str) -> str:
    if not text.strip():
        raise ValueError("empty text")

    return text


def has_text(path: Path) -> bool:
    if not path.is_file():
        return False

    return bool(read_text(path).strip())


def decision_data(slug: str, role: str, text: str, run: Run) -> dict[str, Any]:
    return {
        "id": f"{slug}-proposal-approve",
        "target": f"project/{slug}/proposal",
        "actor": role,
        "role": role,
        "decision": "approved",
        "reason": text,
        "time": now_text(),
        "run": run.run_dir,
    }


def approve_proposal(
    root: Path, slug: str, role: str, text: str, run: Run
) -> list[Path]:
    slug_ok(slug)
    text = ensure_text(text)
    folder = project_path(root, slug)
    proposal = proposal_path(root, slug)

    if not has_text(proposal / "main.tex"):
        raise FileNotFoundError(str(proposal / "main.tex"))

    project = read_map(folder / "meta.yaml")
    data = read_map(proposal / "meta.yaml")

    if project.get("slug") != slug:
        raise ValueError("project slug mismatch")

    if data.get("project") != slug:
        raise ValueError("proposal slug mismatch")

    decision = decision_data(slug, role, text, run)
    project["state"] = "active"
    project["approved"] = decision["time"]
    data["state"] = "approved"
    data["approved"] = decision["time"]

    output: list[Path] = []
    output.append(Path(write_yaml(str(proposal / "decision.yaml"), decision)))
    output.append(Path(write_yaml(str(folder / "meta.yaml"), project)))
    output.append(Path(write_yaml(str(proposal / "meta.yaml"), data)))
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
    if len(argv) < 5:
        raise ValueError("usage: approve.py ROOT SLUG ROLE TEXT")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    role = argv[3]
    text = " ".join(argv[4:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug, "role": role},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = approve_proposal(root, slug, role, text, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "role": role,
                "output": [str(path) for path in output],
            },
        )

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
