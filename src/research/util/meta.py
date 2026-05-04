from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any


def sha_hex(data: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def read_byte(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()


def json_byte(data: Any) -> bytes:
    text = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def tree_hash(root: str) -> str:
    path_list: list[str] = []
    for folder, _, file_list in os.walk(root):
        file_list.sort()
        for name in file_list:
            path_list.append(os.path.join(folder, name))

    path_list.sort()
    hasher = hashlib.sha256()

    for path in path_list:
        rel = os.path.relpath(path, root).replace(os.sep, "/").encode("utf-8")
        hasher.update(rel)
        hasher.update(b"\0")
        hasher.update(read_byte(path))
        hasher.update(b"\0")

    return hasher.hexdigest()


def build_meta(
    params: dict[str, Any], env: str, script: str, src: str, config: str | None
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    meta_path = __file__

    param_sha = sha_hex(json_byte(params))
    env_sha = sha_hex(read_byte(env))
    script_sha = sha_hex(read_byte(script))
    config_sha = sha_hex(read_byte(config)) if config is not None else sha_hex(b"")
    meta_sha = sha_hex(read_byte(meta_path))
    src_sha = tree_hash(src)

    finger = sha_hex(
        (param_sha + env_sha + script_sha + config_sha + meta_sha + src_sha).encode(
            "utf-8"
        )
    )[:16]

    return {
        "timestamp": timestamp,
        "params": params,
        "env": env,
        "script": script,
        "config": config,
        "src": src,
        "sha": {
            "params": param_sha,
            "env": env_sha,
            "script": script_sha,
            "config": config_sha,
            "meta": meta_sha,
            "src": src_sha,
        },
        "fingerprint": finger,
    }
