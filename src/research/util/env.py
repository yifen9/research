from __future__ import annotations

import hashlib
from pathlib import Path

from research.io.text import read_text


def env_path() -> Path:
    return Path("/etc/research/env.sha")


def env_sha(root: Path) -> str:
    hasher = hashlib.sha256()

    for name in ["Dockerfile", "build.yaml"]:
        path = root / "infra" / "docker" / "profile" / "full" / name
        hasher.update(path.read_bytes())

    hasher.update((root / "uv.lock").read_bytes())
    return hasher.hexdigest()


def image_sha() -> str:
    return read_text(env_path()).strip()
