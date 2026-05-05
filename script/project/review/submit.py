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


ROLE = {"architect", "manager", "reviewer"}


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


def state_text(decision: str) -> str:
    if decision in {"accept", "accepted"}:
        return "accepted"

    if decision in {"reject", "rejected"}:
        return "rejected"

    raise ValueError("bad decision")


def result_path(root: Path, slug: str, result: str) -> Path:
    return root / "project" / slug / "result" / result / "meta.yaml"


def review_path(root: Path, slug: str, result: str) -> Path:
    return root / "project" / slug / "review" / result / "meta.yaml"


def experiment_path(root: Path, slug: str, experiment: str) -> Path:
    return root / "project" / slug / "experiment" / experiment / "meta.yaml"


def review_data(
    root: Path,
    slug: str,
    result: str,
    role: str,
    decision: str,
    text: str,
    run: Run,
) -> dict[str, Any]:
    time = now_text()
    return {
        "id": result,
        "project": slug,
        "kind": "review",
        "target": f"project/{slug}/result/{result}",
        "reviewer": role,
        "role": role,
        "decision": decision,
        "reason": text,
        "risk": [],
        "run": run.run_dir,
        "branch": branch_text(root),
        "base": base_text(root),
        "created": time,
        "updated": time,
    }


def submit_review(
    root: Path,
    slug: str,
    result: str,
    role: str,
    decision: str,
    text: str,
    run: Run,
) -> Path:
    slug_ok(slug)
    slug_ok(result)
    role_ok(role)

    if not text.strip():
        raise ValueError("empty text")

    decision = state_text(decision)
    path = result_path(root, slug, result)
    data = read_map(path)
    experiment = str(data["experiment"])
    experiment_file = experiment_path(root, slug, experiment)
    experiment_data = read_map(experiment_file)
    review = review_path(root, slug, result)

    if data.get("state") not in {"submitted", "review"}:
        raise ValueError("result is not submitted")

    if review.exists():
        raise FileExistsError(str(review))

    time = now_text()
    data["state"] = decision
    data["review"] = f"project/{slug}/review/{result}/meta.yaml"
    data["updated"] = time
    experiment_data["state"] = decision
    experiment_data["review"] = data["review"]
    experiment_data["updated"] = time
    review.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(str(path), data)
    write_yaml(str(experiment_file), experiment_data)
    return Path(
        write_yaml(
            str(review), review_data(root, slug, result, role, decision, text, run)
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
    if len(argv) < 7:
        raise ValueError("usage: submit.py ROOT SLUG RESULT ROLE DECISION TEXT")

    root = Path(argv[1]).resolve()
    slug = argv[2]
    result = argv[3]
    role = argv[4]
    decision = argv[5]
    text = " ".join(argv[6:])
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
        output = submit_review(root, slug, result, role, decision, text, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "result": result,
                "decision": decision,
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
        fail(run, "review", error)


if __name__ == "__main__":
    main(sys.argv)
