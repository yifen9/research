from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.agent.provider import Req, make_provider
from research.io.text import read_text, write_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def read_conf(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def latest_dir(target: Path) -> str:
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    data = [path.name for path in sorted(target.iterdir()) if path.is_dir()]

    if not data:
        raise FileNotFoundError(str(target))

    return data[-1]


def bundle_path(bundle_dir: Path, bundle: str, role: str) -> Path:
    if bundle == "latest":
        bundle = latest_dir(bundle_dir)

    path = bundle_dir / bundle / f"{role}.md"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path


def change_path(change_dir: Path, change: str) -> Path:
    if change == "latest":
        change = latest_dir(change_dir)

    path = change_dir / change

    if not path.is_dir():
        raise NotADirectoryError(str(path))

    return path


def write_resp(path: Path, text: str) -> Path:
    return write_text(path, text.rstrip() + "\n")


def run_worker(
    conf: Path,
    bundle_dir: Path,
    change_dir: Path,
    bundle: str,
    change: str,
) -> dict[str, Any]:
    data = read_conf(conf)
    provider = make_provider(data)
    bundle_file = bundle_path(bundle_dir, bundle, "worker")
    change_root = change_path(change_dir, change)
    text = read_text(bundle_file)

    resp = provider.send(
        Req(
            role="worker",
            text=text,
            meta={
                "bundle": str(bundle_file),
                "change": str(change_root),
            },
        )
    )

    proposal = change_root / "proposal.md"
    raw = change_root / "worker.md"

    write_resp(proposal, resp.text)
    write_resp(raw, resp.text)

    return {
        "provider": resp.provider,
        "model": resp.model,
        "bundle": str(bundle_file),
        "change": str(change_root),
        "proposal": str(proposal),
        "raw": str(raw),
        "size": len(resp.text),
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
    if len(argv) != 7:
        raise ValueError(
            "usage: worker.py ROOT CONFIG BUNDLE_DIR CHANGE_DIR BUNDLE CHANGE"
        )

    root = Path(argv[1]).resolve()
    conf = Path(argv[2])
    bundle_dir = Path(argv[3])
    change_dir = Path(argv[4])
    bundle = argv[5]
    change = argv[6]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "config": str(conf),
            "bundle_dir": str(bundle_dir),
            "change_dir": str(change_dir),
            "bundle": bundle,
            "change": change,
        },
        script=script,
        src=root / "src",
        config=conf,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "worker",
                "start",
                {
                    "root": str(root),
                    "config": str(conf),
                    "bundle_dir": str(bundle_dir),
                    "change_dir": str(change_dir),
                    "bundle": bundle,
                    "change": change,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = run_worker(conf, bundle_dir, change_dir, bundle, change)

        run.logger.info(
            jline(
                "script",
                "worker",
                "ok",
                {
                    "provider": data["provider"],
                    "model": data["model"],
                    "proposal": data["proposal"],
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                **data,
            },
        )

    except (
        ValueError,
        KeyError,
        FileExistsError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
        NotImplementedError,
    ) as error:
        fail(run, "worker", error)


if __name__ == "__main__":
    main(sys.argv)
