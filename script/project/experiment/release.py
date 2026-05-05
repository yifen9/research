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


def claim_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "claim.yaml"


def role_release(claim_role: str, role: str) -> bool:
    role_ok(claim_role)
    role_ok(role)
    return ROLE[role] >= ROLE[claim_role]


def release_experiment(
    root: Path,
    slug: str,
    experiment: str,
    role: str,
    reason: str,
    run: Run,
) -> Path:
    slug_ok(slug)
    slug_ok(experiment)
    role_ok(role)

    if not reason.strip():
        raise ValueError("empty reason")

    path = claim_path(root, slug, experiment)
    data = read_map(path)

    if data.get("state") != "claimed":
        raise ValueError("experiment is not claimed")

    if not role_release(str(data["role"]), role):
        raise ValueError("role cannot release")

    time = now_text()
    data["state"] = "released"
    data["released"] = time
    data["updated"] = time
    data["release_role"] = role
    data["release_run"] = run.run_dir
    data["reason"] = reason
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
        raise ValueError("usage: release.py ROOT SLUG EXPERIMENT ROLE REASON")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    experiment = argv[3]
    role = argv[4]
    reason = " ".join(argv[5:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug, "experiment": experiment},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = release_experiment(root, slug, experiment, role, reason, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "experiment": experiment,
                "output": [str(output)],
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        TypeError,
    ) as error:
        fail(run, "experiment", error)


if __name__ == "__main__":
    main(sys.argv)
