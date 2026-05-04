from __future__ import annotations

from pathlib import Path

from research.io.text import read_text, write_text
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress


def skip_path(path: Path) -> bool:
    for part in path.parts:
        if part.startswith("."):
            return True

    return False


def clean_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

    for item in path.rglob("*.md"):
        item.unlink()


def md_list(source: Path) -> list[Path]:
    if not source.is_dir():
        raise NotADirectoryError(str(source))

    data: list[Path] = []

    for path in sorted(source.rglob("*.md")):
        rel = path.relative_to(source)

        if skip_path(rel):
            continue

        data.append(path)

    if not data:
        raise FileNotFoundError(str(source))

    return data


def copy_md(source: Path, target: Path, logger: Logger) -> list[Path]:
    data = md_list(source)
    output: list[Path] = []
    progress = make_progress(logger, "mirror", len(data))

    progress.start()

    for path in data:
        rel = path.relative_to(source)
        out = target / rel
        text = read_text(path)
        output.append(write_text(out, text))
        logger.info(
            jline(
                "mirror",
                "write",
                "copy",
                {
                    "source": str(path),
                    "target": str(out),
                },
            )
        )
        progress.step(1)

    progress.finish()
    return output


def title_text(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def manifest_text(source: Path, target: Path, output: list[Path]) -> str:
    body: list[str] = []

    body.append(f"# {title_text(target.name)} Manifest\n")
    body.append("## Purpose\n")
    body.append("This directory contains generated agent-readable workflow context.\n")
    body.append("## Source\n")
    body.append(f"- source: {source}")
    body.append(f"- target: {target}")
    body.append(f"- count: {len(output)}")
    body.append("\n## File\n")

    for path in output:
        rel = path.relative_to(target)
        body.append(f"- [{rel}](./{rel})")

    body.append("\n## Rule\n")
    body.append("- Source files are maintained outside context/.")
    body.append("- Generated context files should not be edited manually.")
    body.append("- Regenerate this directory with the corresponding script.")
    body.append("")

    return "\n".join(body)


def write_manifest(source: Path, target: Path, output: list[Path]) -> Path:
    path = target / "_manifest.md"
    text = manifest_text(source, target, output)
    return write_text(path, text)


def write_mirror(source: Path, target: Path, logger: Logger) -> list[Path]:
    clean_dir(target)
    output = copy_md(source, target, logger)
    output.append(write_manifest(source, target, output))
    return output
