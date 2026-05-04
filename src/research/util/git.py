from __future__ import annotations

from pathlib import Path
import subprocess


def run_cmd(root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )

    return proc.stdout + proc.stderr


def git_hash(root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )

    return proc.stdout.strip()


def git_status(root: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )

    return proc.stdout


def commit_msg(title: str) -> str:
    text = title.strip()

    if not text:
        raise ValueError("empty title")

    return f"agent: {text}"


def git_commit(root: Path, title: str) -> str:
    status = git_status(root)

    if not status.strip():
        raise RuntimeError("no git change to commit")

    run_cmd(root, ["git", "add", "-A"])
    run_cmd(root, ["git", "commit", "-m", commit_msg(title)])

    return git_hash(root)
