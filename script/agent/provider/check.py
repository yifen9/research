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


def check_text(resp: Any) -> str:
    body: list[str] = []

    body.append("# Provider Check\n")
    body.append("## Meta\n")
    body.append("```yaml")
    body.append(
        yaml_text(
            {
                "provider": resp.provider,
                "model": resp.model,
                "meta": resp.meta,
            }
        ).rstrip()
    )
    body.append("```\n")
    body.append("## Text\n")
    body.append(resp.text.rstrip())
    body.append("")

    return "\n".join(body)


def run_check(conf: Path, source: Path, target: Path) -> Path:
    data = read_conf(conf)
    provider = make_provider(data)
    text = read_text(source)
    req = Req(
        role="check",
        text=text,
        meta={
            "source": str(source),
            "target": str(target),
        },
    )
    resp = provider.send(req)
    return write_text(target, check_text(resp))


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
    if len(argv) != 5:
        raise ValueError("usage: check.py ROOT CONFIG SOURCE TARGET")

    root = Path(argv[1]).resolve()
    conf = Path(argv[2])
    source = Path(argv[3])
    target = Path(argv[4])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "config": str(conf),
            "source": str(source),
            "target": str(target),
        },
        script=script,
        src=root / "src",
        config=conf,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "provider",
                "start",
                {
                    "root": str(root),
                    "config": str(conf),
                    "source": str(source),
                    "target": str(target),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        path = run_check(conf, source, target)

        run.logger.info(
            jline(
                "script",
                "provider",
                "ok",
                {
                    "path": str(path),
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "config": str(conf),
                "source": str(source),
                "target": str(path),
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
        NotImplementedError,
    ) as error:
        fail(run, "provider", error)


if __name__ == "__main__":
    main(sys.argv)
