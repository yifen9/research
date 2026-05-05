from __future__ import annotations

import subprocess

from research.agent.backend import BackendSpec


def run_check(call: list[str]) -> int:
    result = subprocess.run(call, check=False, capture_output=True)
    return result.returncode


def check_backend(data: BackendSpec) -> list[list[str]]:
    bad: list[list[str]] = []

    for call in data.check:
        if run_check(call) != 0:
            bad.append(call)

    return bad
