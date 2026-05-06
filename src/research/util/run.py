from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any

import yaml

from research.io.json import write_json
from research.io.text import read_text, write_text
from research.util.audit import Audit
from research.util.console import make_console
from research.util.logger import Logger, make_logger
from research.util.meta import build_meta
from research.util.versioner import make_dir


@dataclass(slots=True)
class Run:
    run_dir: str
    meta: dict[str, Any]
    audit: Audit
    logger: Logger
    summary_path: Path


def task_name(root: Path, script: Path) -> str:
    rel = script.relative_to(root)
    part = list(rel.with_suffix("").parts)
    return "-".join(part)


def env_text() -> str:
    body: list[str] = []

    for key, value in sorted(os.environ.items()):
        body.append(f"{key}={env_value(key, value)}")

    return "\n".join(body) + "\n"


def env_value(key: str, value: str) -> str:
    if re.search(r"(?i)password|passwd|pwd|secret|token|key|credential", key):
        return "[REDACTED]"

    value = re.sub(r"(?i)(password|passwd|pwd|secret|token|api[_-]?key)(\s*[:=]\s*)([^\s,;]+)", r"\1\2[REDACTED]", value)
    value = re.sub(r"(?i)bearer\s+[a-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
    value = re.sub(r"\b[A-Za-z0-9_=-]{32,}\b", "[REDACTED]", value)
    return value


def write_env(root: Path, name: str) -> Path:
    path = root / "out" / "temp" / "env" / f"{name}.txt"
    return write_text(path, env_text())


def save_env(temp_env: Path, run_dir: str) -> Path:
    path = Path(run_dir) / "_env.txt"
    text = read_text(temp_env)
    return write_text(path, text)


def save_meta(run_dir: str, meta: dict[str, Any]) -> Path:
    path = Path(run_dir) / "_meta.json"
    write_json(str(path), meta)
    return path


def yaml_block(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def list_block(data: list[Any]) -> str:
    body: list[str] = []

    for item in data:
        body.append("```yaml")
        body.append(yaml_block(item).rstrip())
        body.append("```")

    return "\n\n".join(body)


def summary_text(
    run: Run,
    status: str,
    data: dict[str, Any],
    error: BaseException | None,
) -> str:
    body: list[str] = []

    body.append("# Run Summary\n")
    body.append("## Status\n")
    body.append(f"- status: {status}")
    body.append(f"- run: {run.run_dir}")
    body.append(f"- fingerprint: {run.meta['fingerprint']}")
    body.append(f"- timestamp: {run.meta['timestamp']}")
    body.append(f"- env: {run.run_dir}/_env.txt")
    body.append(f"- audit: {run.run_dir}/_audit.json")
    body.append(f"- meta: {run.run_dir}/_meta.json")
    body.append(f"- log: {run.run_dir}/_log")

    if error is not None:
        body.append(f"- error_type: {type(error).__name__}")
        body.append(f"- error_message: {str(error)}")

    body.append("\n## Data\n")
    body.append("```yaml")
    body.append(yaml_block(data).rstrip())
    body.append("```")

    if "stat" in data:
        body.append("\n## Stat\n")
        body.append("```yaml")
        body.append(yaml_block(data["stat"]).rstrip())
        body.append("```")

    if "top_kind" in data:
        body.append("\n## Top Kind\n")
        body.append("```yaml")
        body.append(yaml_block(data["top_kind"]).rstrip())
        body.append("```")

    if "top_path" in data:
        body.append("\n## Top Path\n")
        body.append("```yaml")
        body.append(yaml_block(data["top_path"]).rstrip())
        body.append("```")

    if "bad" in data:
        body.append("\n## Violation\n")
        body.append(list_block(data["bad"]))

    if "next" in data:
        body.append("\n## Next\n")
        for item in data["next"]:
            body.append(f"- {item}")

    body.append("")
    return "\n".join(body)


def write_summary(
    run: Run,
    status: str,
    data: dict[str, Any],
    error: BaseException | None,
) -> Path:
    text = summary_text(run, status, data, error)
    return write_text(run.summary_path, text)


def make_run(
    root: Path,
    name: str,
    params: dict[str, Any],
    script: Path,
    src: Path,
    config: Path | None,
) -> Run:
    temp_env = write_env(root, name)

    meta = build_meta(
        params=params,
        env=str(temp_env),
        script=str(script),
        src=str(src),
        config=str(config) if config is not None else None,
    )

    run_dir = make_dir(str(root / "out" / "run"), meta)
    env_path = save_env(temp_env, run_dir)
    meta["env"] = str(env_path)
    save_meta(run_dir, meta)

    audit = Audit.create(run_dir, meta)
    logger = make_logger([make_console(False), audit])
    summary_path = Path(run_dir) / "_summary.md"

    run = Run(
        run_dir=run_dir,
        meta=meta,
        audit=audit,
        logger=logger,
        summary_path=summary_path,
    )

    write_summary(run, "running", {"task": name}, None)
    return run


def run_ok(run: Run, data: dict[str, Any]) -> None:
    run.audit.finish_ok()
    write_summary(run, "success", data, None)


def run_err(run: Run, error: BaseException, data: dict[str, Any]) -> None:
    run.audit.finish_err(error)
    write_summary(run, "error", data, error)
