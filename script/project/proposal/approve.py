from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
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


def decision_data(
    slug: str, role: str, text: str, branch: str, run: Run
) -> dict[str, Any]:
    message = commit_message(slug, run)
    return {
        "id": f"{slug}-proposal-approve",
        "target": f"project/{slug}/proposal",
        "actor": role,
        "role": role,
        "decision": "approved",
        "reason": text,
        "branch": branch,
        "commit": {
            "required": True,
            "message": message[0],
            "body": message[1],
            "branch": branch,
        },
        "time": now_text(),
        "run": run.run_dir,
    }


def commit_message(slug: str, run: Run) -> list[str]:
    return [
        f"approve project proposal for {slug}",
        "\n".join(
            [
                "Records durable approval for the project proposal so the project can move from proposal to active state.",
                "",
                f"Decision: project/{slug}/proposal/decision.yaml",
                f"Run: {run.run_dir}",
            ]
        ),
    ]


def branch_name(slug: str) -> str:
    return f"project/{slug}/approve"


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


def git_other(root: Path, target: str) -> list[str]:
    text = git_call(root, ["status", "--porcelain"])
    data: list[str] = []

    for line in text.splitlines():
        path = line[3:]

        if not path.startswith(target):
            data.append(line)

    return data


def git_has(root: Path, name: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode not in {0, 1}:
        raise RuntimeError((result.stdout + result.stderr).strip())

    return result.returncode == 0


def git_branch(root: Path) -> str:
    return git_call(root, ["branch", "--show-current"])


def set_branch(root: Path, name: str) -> str:
    current = git_branch(root)

    if current == name:
        return current

    if git_has(root, name):
        git_call(root, ["switch", name])
    else:
        git_call(root, ["switch", "-c", name])

    return git_branch(root)


def git_ok(root: Path, slug: str) -> str:
    target = f"project/{slug}"
    other = git_other(root, target)

    if other:
        raise RuntimeError("unrelated dirty worktree")

    return set_branch(root, branch_name(slug))


def git_commit(root: Path, slug: str, branch: str, run: Run) -> dict[str, str]:
    target = f"project/{slug}"
    message = commit_message(slug, run)
    git_call(root, ["add", "--", target])
    git_call(root, ["commit", "-m", message[0], "-m", message[1], "--", target])
    return {
        "sha": git_call(root, ["rev-parse", "HEAD"]),
        "branch": branch,
    }


def approve_proposal(
    root: Path, slug: str, role: str, text: str, run: Run
) -> dict[str, Any]:
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

    branch = git_ok(root, slug)
    decision = decision_data(slug, role, text, branch, run)
    project["state"] = "active"
    project["approved"] = decision["time"]
    data["state"] = "approved"
    data["approved"] = decision["time"]

    output: list[Path] = []
    output.append(Path(write_yaml(str(proposal / "decision.yaml"), decision)))
    output.append(Path(write_yaml(str(folder / "meta.yaml"), project)))
    output.append(Path(write_yaml(str(proposal / "meta.yaml"), data)))
    commit = git_commit(root, slug, branch, run)
    return {
        "commit": commit,
        "output": [str(path) for path in output],
    }


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
        data = approve_proposal(root, slug, role, text, run)
        run_ok(
            run,
            {
                "task": task,
                "slug": slug,
                "role": role,
                **data,
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
