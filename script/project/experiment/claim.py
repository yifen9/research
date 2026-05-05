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


ROLE = {"architect", "manager", "reviewer", "worker"}


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


def session_path(root: Path, role: str, name: str) -> Path:
    return root / "out" / "agent" / "session" / role / name / "session.yaml"


def current_session(root: Path, role: str) -> str:
    base = root / "out" / "agent" / "session" / role

    if not base.is_dir():
        raise FileNotFoundError(str(base))

    data: list[str] = []

    for folder in sorted(base.iterdir()):
        if not folder.is_dir():
            continue

        item = read_map(folder / "session.yaml")

        if item.get("state") == "active":
            data.append(folder.name)

    if not data:
        raise FileNotFoundError("active session")

    return data[-1]


def session_name(root: Path, role: str, name: str) -> str:
    if name == "current":
        return current_session(root, role)

    return name


def session_ok(root: Path, role: str, name: str) -> None:
    path = session_path(root, role, name)

    if not path.is_file():
        return

    data = read_map(path)

    if data.get("state") == "retired":
        raise ValueError("session is retired")


def claim_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "claim.yaml"


def project_ok(root: Path, slug: str) -> None:
    data = read_map(root / "project" / slug / "meta.yaml")

    if data.get("slug") != slug:
        raise ValueError("project slug mismatch")


def claim_data(
    root: Path,
    slug: str,
    experiment: str,
    role: str,
    session: str,
    run: Run,
) -> dict[str, Any]:
    time = now_text()
    return {
        "id": f"{slug}-{experiment}-claim",
        "project": slug,
        "experiment": experiment,
        "kind": "experiment-claim",
        "state": "claimed",
        "role": role,
        "session": session,
        "run": run.run_dir,
        "branch": branch_text(root),
        "base": base_text(root),
        "target": f"project/{slug}/experiment/{experiment}",
        "created": time,
        "updated": time,
    }


def claim_experiment(
    root: Path,
    slug: str,
    experiment: str,
    role: str,
    session: str,
    run: Run,
) -> Path:
    slug_ok(slug)
    slug_ok(experiment)
    role_ok(role)
    session = session_name(root, role, session)
    session_ok(root, role, session)
    project_ok(root, slug)
    path = claim_path(root, slug, experiment)

    if path.is_file():
        data = read_map(path)
        if data.get("state") == "claimed":
            raise ValueError("experiment is claimed")

    path.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        write_yaml(str(path), claim_data(root, slug, experiment, role, session, run))
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
    if len(argv) != 6:
        raise ValueError("usage: claim.py ROOT SLUG EXPERIMENT ROLE SESSION")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    experiment = argv[3]
    role = argv[4]
    session = argv[5]
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
        output = claim_experiment(root, slug, experiment, role, session, run)
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
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "experiment", error)


if __name__ == "__main__":
    main(sys.argv)
