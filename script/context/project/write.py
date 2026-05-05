from __future__ import annotations

from pathlib import Path
import sys

from research.io.text import write_text
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress
from research.util.run import Run, make_run, run_err, run_ok, task_name


def skip_path(path: Path) -> bool:
    skip = {
        ".git",
        ".github",
        ".quarto",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "_extensions",
        "build",
        "out",
    }

    for part in path.parts:
        if part in skip:
            return True

        if part.endswith(".egg-info"):
            return True

    return False


def clean_target(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)

    for path in target.glob("*.md"):
        path.unlink()


def top_entry(root: Path) -> list[Path]:
    data: list[Path] = []

    for path in sorted(root.iterdir()):
        rel = path.relative_to(root)

        if skip_path(rel):
            continue

        data.append(path)

    return data


def entry_kind(path: Path) -> str:
    if path.is_dir():
        return "dir"

    if path.is_file():
        return "file"

    return "other"


def tree_line(root: Path, path: Path, depth: int) -> str:
    rel = path.relative_to(root)
    indent = "  " * depth
    return f"{indent}- {rel.name}"


def scan_tree(root: Path, path: Path, depth: int, limit: int) -> list[str]:
    body: list[str] = []

    if depth > limit:
        return body

    if skip_path(path.relative_to(root)):
        return body

    body.append(tree_line(root, path, depth))

    if path.is_dir():
        for item in sorted(path.iterdir()):
            body.extend(scan_tree(root, item, depth + 1, limit))

    return body


def make_manifest(root: Path, target: Path, limit: int) -> str:
    body: list[str] = []

    body.append("# Project Manifest\n")
    body.append("## Purpose\n")
    body.append(
        "This directory describes the research repository as a meta-infrastructure project.\n"
    )
    body.append("## File\n")
    body.append("- [Overview](./overview.md)")
    body.append("- [Structure](./structure.md)")
    body.append("\n## Source\n")
    body.append(f"- root: {root}")
    body.append(f"- target: {target}")
    body.append(f"- depth: {limit}")
    body.append("\n## Rule\n")
    body.append(
        "- The research repository is the meta repository for rules, context, infrastructure, and agent workflow."
    )
    body.append("- Do not edit generated context/project files manually.")
    body.append("- Regenerate this directory with context-project-write.")
    body.append("")

    return "\n".join(body)


def make_overview(root: Path, target: Path) -> str:
    data = top_entry(root)
    body: list[str] = []

    body.append("# Project Overview\n")
    body.append("## Identity\n")
    body.append(
        "This repository is a meta-infrastructure repository for research work.\n"
    )
    body.append("## Role\n")
    body.append("- Maintains machine-readable rules.")
    body.append("- Generates agent-readable context.")
    body.append("- Builds development infrastructure.")
    body.append(
        "- Records runs with audit, metadata, logs, fingerprints, and summaries."
    )
    body.append("- Prepares the base for worker-reviewer-human agent workflows.\n")
    body.append("## Boundary\n")
    body.append("- src/ contains reusable internal library code.")
    body.append("- script/ contains executable task entrypoints.")
    body.append("- context/ contains generated or maintained agent-readable knowledge.")
    body.append("- out/ contains generated runtime artifacts and disposable outputs.")
    body.append("- rule/ contains the source of governance rules.")
    body.append("- infra/ contains infrastructure definitions.\n")
    body.append("## Top Entry\n")
    body.append("| Name | Kind |")
    body.append("|---|---|")

    for path in data:
        body.append(f"| {path.name} | {entry_kind(path)} |")

    body.append("")
    body.append("## Target\n")
    body.append(f"- context: {target}")
    body.append("")

    return "\n".join(body)


def make_structure(root: Path, limit: int) -> str:
    body: list[str] = []

    body.append("# Project Structure\n")
    body.append("## Tree\n")

    for path in top_entry(root):
        body.extend(scan_tree(root, path, 0, limit))

    body.append("")
    body.append("## Note\n")
    body.append(
        "- This tree excludes generated, cache, hidden-tool, and runtime directories."
    )
    body.append(
        "- Full repository inspection should use the repository itself, not this summary."
    )
    body.append("")

    return "\n".join(body)


def write_project(root: Path, target: Path, limit: int, logger: Logger) -> list[Path]:
    output: list[Path] = []
    progress = make_progress(logger, "project", 3)

    clean_target(target)
    progress.start()

    path = target / "_manifest.md"
    output.append(write_text(path, make_manifest(root, target, limit)))
    logger.info(jline("context", "project", "write", {"path": str(path)}))
    progress.step(1)

    path = target / "overview.md"
    output.append(write_text(path, make_overview(root, target)))
    logger.info(jline("context", "project", "write", {"path": str(path)}))
    progress.step(1)

    path = target / "structure.md"
    output.append(write_text(path, make_structure(root, limit)))
    logger.info(jline("context", "project", "write", {"path": str(path)}))
    progress.step(1)

    progress.finish()
    return output


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
    if len(argv) != 4:
        raise ValueError("usage: write.py ROOT TARGET DEPTH")

    root = Path(argv[1]).resolve()
    target = Path(argv[2])
    limit = int(argv[3])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "target": str(target),
            "depth": limit,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "project",
                "start",
                {
                    "root": str(root),
                    "target": str(target),
                    "depth": limit,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_project(root, target, limit, run.logger)

        run.logger.info(
            jline(
                "script",
                "project",
                "ok",
                {
                    "output": len(output),
                    "target": str(target),
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "target": str(target),
                "depth": limit,
                "output": len(output),
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
        fail(run, "project", error)


if __name__ == "__main__":
    main(sys.argv)
