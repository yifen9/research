from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.text import read_text, write_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress
from research.util.run import Run, make_run, run_err, run_ok, task_name


def bind_text(text: str, data: dict[str, Any]) -> str:
    output = text

    for name, value in data["version"].items():
        key = "{{" + name + "}}"
        output = output.replace(key, str(value))

    return output


def make_docker(root: Path, profile: str, data: dict[str, Any], logger: Logger) -> str:
    body: list[str] = []
    part = data["part"]
    progress = make_progress(logger, "docker", len(part))

    logger.info(jline("docker", "write", "make", {"profile": profile}))
    body.append(f"FROM {data['image']['base']}\n")
    progress.start()

    for name in part:
        path = root / "infra" / "docker" / "part" / name / "Dockerfile"
        logger.info(jline("docker", "write", "part", {"name": name, "path": str(path)}))
        text = read_text(path)
        body.append(bind_text(text, data))
        body.append("")
        progress.step(1)

    progress.finish()
    body.append("WORKDIR /workspace\n")

    return "\n".join(body)


def read_build(root: Path, profile: str, logger: Logger) -> dict[str, Any]:
    path = root / "infra" / "docker" / "profile" / profile / "build.yaml"
    logger.info(jline("docker", "write", "read", {"path": str(path)}))
    return read_yaml(str(path))


def write_docker(root: Path, profile: str, logger: Logger) -> Path:
    data = read_build(root, profile, logger)
    text = make_docker(root, profile, data, logger)
    path = root / "infra" / "docker" / "profile" / profile / "Dockerfile"
    logger.info(jline("docker", "write", "save", {"path": str(path)}))
    return write_text(path, text)


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
    if len(argv) != 3:
        raise ValueError("usage: write.py ROOT PROFILE")

    root = Path(argv[1]).resolve()
    profile = argv[2]
    script = Path(__file__).resolve()
    task = task_name(root, script)
    config = root / "infra" / "docker" / "profile" / profile / "build.yaml"

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "profile": profile,
        },
        script=script,
        src=root / "src",
        config=config,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "docker",
                "start",
                {
                    "root": str(root),
                    "profile": profile,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        path = write_docker(root, profile, run.logger)

        run.logger.info(
            jline(
                "script",
                "docker",
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
                "path": str(path),
                "profile": profile,
            },
        )

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "docker", error)


if __name__ == "__main__":
    main(sys.argv)
