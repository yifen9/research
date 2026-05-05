from __future__ import annotations

from pathlib import Path
import subprocess


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


def commit_sha(root: Path) -> str:
    return git_call(root, ["rev-parse", "HEAD"])


def branch_name(root: Path) -> str:
    return git_call(root, ["branch", "--show-current"])


def clean_check(root: Path) -> bool:
    return git_call(root, ["status", "--porcelain"]) == ""
