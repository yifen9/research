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


ROLE = {"worker"}


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


def claim_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "claim.yaml"


def experiment_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "meta.yaml"


def result_path(root: Path, slug: str, result: str) -> Path:
    return root / "project" / slug / "result" / result / "meta.yaml"


def claim_ok(
    root: Path, slug: str, experiment: str, role: str, session: str
) -> dict[str, Any]:
    data = read_map(claim_path(root, slug, experiment))

    if data.get("state") != "claimed":
        raise ValueError("experiment is not claimed")

    if data.get("role") != role:
        raise ValueError("claim role mismatch")

    if data.get("session") != session:
        raise ValueError("claim session mismatch")

    return data


def experiment_ok(root: Path, slug: str, experiment: str) -> dict[str, Any]:
    data = read_map(experiment_path(root, slug, experiment))

    if data.get("project") != slug:
        raise ValueError("experiment project mismatch")

    if data.get("experiment") != experiment:
        raise ValueError("experiment slug mismatch")

    if data.get("state") != "approved":
        raise ValueError("experiment is not approved")

    return data


def result_data(
    root: Path,
    slug: str,
    experiment: str,
    result: str,
    role: str,
    session: str,
    text: str,
    run: Run,
) -> dict[str, Any]:
    time = now_text()
    return {
        "id": result,
        "project": slug,
        "experiment": experiment,
        "kind": "result",
        "state": "submitted",
        "worker": role,
        "role": role,
        "session": session,
        "run": run.run_dir,
        "branch": branch_text(root),
        "base": base_text(root),
        "target": f"project/{slug}/result/{result}",
        "claim": f"project/{slug}/experiment/{experiment}/claim.yaml",
        "output": text,
        "check": [],
        "created": time,
        "updated": time,
    }


def submit_result(
    root: Path,
    slug: str,
    experiment: str,
    result: str,
    role: str,
    session: str,
    text: str,
    run: Run,
) -> Path:
    slug_ok(slug)
    slug_ok(experiment)
    slug_ok(result)
    role_ok(role)

    if not text.strip():
        raise ValueError("empty text")

    claim_ok(root, slug, experiment, role, session)
    data = experiment_ok(root, slug, experiment)
    path = result_path(root, slug, result)

    if path.exists():
        raise FileExistsError(str(path))

    data["state"] = "result"
    data["result"] = f"project/{slug}/result/{result}/meta.yaml"
    data["updated"] = now_text()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(str(experiment_path(root, slug, experiment)), data)
    return Path(
        write_yaml(
            str(path),
            result_data(root, slug, experiment, result, role, session, text, run),
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
        raise ValueError(
            "usage: submit.py ROOT SLUG EXPERIMENT RESULT ROLE SESSION TEXT"
        )

    root = Path(argv[1]).resolve()
    slug = argv[2]
    experiment = argv[3]
    result = argv[4]
    role = argv[5]
    session = argv[6]
    text = " ".join(argv[7:])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task, "slug": slug, "result": result},
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        output = submit_result(root, slug, experiment, result, role, session, text, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "experiment": experiment,
                "result": result,
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
        fail(run, "result", error)


if __name__ == "__main__":
    main(sys.argv)
