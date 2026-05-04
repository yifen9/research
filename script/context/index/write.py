from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.text import write_text
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def skip_file(path: Path) -> bool:
    if path.name == "index.md":
        return True

    for part in path.parts:
        if part.startswith("."):
            return True

    return False


def scan_file(target: Path) -> list[Path]:
    data: list[Path] = []

    if not target.is_dir():
        raise NotADirectoryError(str(target))

    for path in sorted(target.rglob("*.md")):
        rel = path.relative_to(target)

        if skip_file(rel):
            continue

        data.append(path)

    if not data:
        raise FileNotFoundError(str(target))

    return data


def split_file(target: Path, data: list[Path]) -> tuple[list[Path], list[Path]]:
    manifest: list[Path] = []
    other: list[Path] = []

    for path in data:
        rel = path.relative_to(target)

        if rel.name == "_manifest.md":
            manifest.append(path)
        else:
            other.append(path)

    return manifest, other


def link_text(target: Path, path: Path) -> str:
    rel = path.relative_to(target)
    name = str(rel)
    return f"[{name}](./{name})"


def make_list(target: Path, data: list[Path]) -> list[str]:
    body: list[str] = []

    for path in data:
        body.append(f"- {link_text(target, path)}")

    return body


def make_tree(target: Path, data: list[Path]) -> list[str]:
    body: list[str] = []

    for path in data:
        rel = path.relative_to(target)
        body.append(f"- {rel}")

    return body


def make_index(target: Path, data: list[Path]) -> str:
    manifest, other = split_file(target, data)
    body: list[str] = []

    body.append("# Context Index\n")
    body.append("## Purpose\n")
    body.append("This directory contains agent-readable context for the research repository.\n")

    body.append("## Read Order\n")
    if manifest:
        body.extend(make_list(target, manifest))
    if other:
        body.extend(make_list(target, other))

    body.append("\n## Manifest\n")
    if manifest:
        body.extend(make_list(target, manifest))
    else:
        body.append("- No manifest found.")

    body.append("\n## File\n")
    if other:
        body.extend(make_list(target, other))
    else:
        body.append("- No additional file found.")

    body.append("\n## Tree\n")
    body.extend(make_tree(target, data))

    body.append("\n## Rule\n")
    body.append("- Read this file first.")
    body.append("- Read manifest files before ordinary context files.")
    body.append("- Do not edit generated context files directly.")
    body.append("- Regenerate context through script/context/* writers.")
    body.append("")

    return "\n".join(body)


def write_index(target: Path, logger: Any) -> Path:
    data = scan_file(target)
    text = make_index(target, data)
    path = target / "index.md"
    logger.info(
        jline(
            "context",
            "index",
            "write",
            {
                "path": str(path),
                "count": len(data),
            },
        )
    )
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
        raise ValueError("usage: write.py ROOT TARGET")

    root = Path(argv[1]).resolve()
    target = Path(argv[2])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "target": str(target),
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "index",
                "start",
                {
                    "root": str(root),
                    "target": str(target),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        path = write_index(target, run.logger)

        run.logger.info(
            jline(
                "script",
                "index",
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
                "target": str(target),
                "path": str(path),
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
    ) as error:
        fail(run, "index", error)


if __name__ == "__main__":
    main(sys.argv)
