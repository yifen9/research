from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

from research.io.yaml import read_yaml, write_yaml
from research.util.env import env_sha
from research.util.git import branch_name, commit_sha
from research.util.jlog import jline
from research.util.lineage import make_lineage
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


def claim_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "claim.yaml"


def experiment_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "meta.yaml"


def result_path(root: Path, slug: str, result: str) -> Path:
    return root / "project" / slug / "result" / result / "meta.yaml"


def claim_ok(
    root: Path,
    slug: str,
    experiment: str,
    role: str,
    session: str,
) -> dict[str, Any]:
    data = read_map(claim_path(root, slug, experiment))

    if data["state"] != "claimed":
        raise ValueError("experiment is not claimed")

    if data["role"] != role:
        raise ValueError("claim role mismatch")

    if data["session"] != session:
        raise ValueError("claim session mismatch")

    return data


def experiment_ok(root: Path, slug: str, experiment: str) -> dict[str, Any]:
    data = read_map(experiment_path(root, slug, experiment))

    if data["project"] != slug:
        raise ValueError("experiment project mismatch")

    if data["experiment"] != experiment:
        raise ValueError("experiment slug mismatch")

    if data["state"] != "approved":
        raise ValueError("experiment is not approved")

    return data


def code_block(root: Path, slug: str) -> dict[str, Any]:
    return {
        "repo": slug,
        "branch": branch_name(root),
        "sha": commit_sha(root),
    }


def env_block(root: Path) -> dict[str, Any]:
    return {
        "image": "ghcr.io/yifen9/research-dev",
        "sha": env_sha(root),
    }


def run_block(run: Run) -> dict[str, Any]:
    return {
        "dir": run.run_dir,
        "fingerprint": run.meta["fingerprint"],
    }


def data_block(meta: dict[str, Any]) -> list[dict[str, Any]]:
    if "data" in meta and isinstance(meta["data"], list):
        return meta["data"]

    return []


def seed_value(meta: dict[str, Any]) -> int:
    if "seed" in meta:
        return int(meta["seed"])

    return 0


def result_data(
    root: Path,
    slug: str,
    experiment: str,
    result: str,
    role: str,
    session: str,
    text: str,
    meta: dict[str, Any],
    run: Run,
) -> dict[str, Any]:
    return {
        "id": result,
        "kind": "result",
        "project": slug,
        "experiment": experiment,
        "state": "submitted",
        "worker": role,
        "session": session,
        "timestamp": now_text(),
        "lineage": make_lineage(
            code=code_block(root, slug),
            data=data_block(meta),
            env=env_block(root),
            seed=seed_value(meta),
            run=run_block(run),
        ),
        "output": text,
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
    meta = experiment_ok(root, slug, experiment)
    path = result_path(root, slug, result)

    if path.exists():
        raise FileExistsError(str(path))

    meta["state"] = "result"
    meta["result"] = f"project/{slug}/result/{result}/meta.yaml"
    meta["updated"] = now_text()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(str(experiment_path(root, slug, experiment)), meta)
    return Path(
        write_yaml(
            str(path),
            result_data(
                root, slug, experiment, result, role, session, text, meta, run
            ),
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
        output = submit_result(
            root, slug, experiment, result, role, session, text, run
        )
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
