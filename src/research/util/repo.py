from __future__ import annotations

from pathlib import Path
import subprocess


def tool_call(tool: str, arg: list[str], dir: Path | None) -> str:
    result = subprocess.run(
        [tool, *arg],
        cwd=dir,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(output)

    return output


def repo_new(name: str, kind: str) -> str:
    if kind not in {"public", "private"}:
        raise ValueError("bad kind")

    return tool_call("gh", ["repo", "create", name, f"--{kind}"], None)


def repo_push(dir: Path, user: str, name: str) -> str:
    url = f"git@github.com:{user}/{name}.git"
    tool_call("git", ["remote", "add", "origin", url], dir)
    return tool_call("git", ["push", "-u", "origin", "main"], dir)
