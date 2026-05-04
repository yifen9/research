from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from research.io.text import read_text, write_text
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def md_list(root: Path) -> list[Path]:
    if not root.is_dir():
        raise NotADirectoryError(str(root))

    data: list[Path] = []

    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)

        if any(part.startswith(".") for part in rel.parts):
            continue

        data.append(path)

    return data


def prompt_list(prompt_dir: Path) -> list[Path]:
    data = md_list(prompt_dir)

    if not data:
        raise FileNotFoundError(str(prompt_dir))

    return data


def context_list(context_dir: Path) -> list[Path]:
    data: list[Path] = []

    index = context_dir / "index.md"

    if not index.is_file():
        raise FileNotFoundError(str(index))

    data.append(index)

    for path in sorted(context_dir.rglob("_manifest.md")):
        data.append(path)

    latest = context_dir / "run" / "latest.md"

    if latest.is_file():
        data.append(latest)

    return data


def change_list(change_dir: Path, change: str) -> list[Path]:
    path = change_dir / change

    if not path.is_dir():
        raise NotADirectoryError(str(path))

    data = md_list(path)

    if not data:
        raise FileNotFoundError(str(path))

    return data


def section(title: str, text: str) -> str:
    return "\n".join(
        [
            f"## {title}",
            "",
            text.rstrip(),
            "",
        ]
    )


def file_section(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    text = read_text(path)
    return section(str(rel), text)


def bundle_text(
    prompt: Path,
    prompt_dir: Path,
    context_dir: Path,
    change_dir: Path,
    change: str,
    context: list[Path],
    change_file: list[Path],
) -> str:
    body: list[str] = []

    body.append("# Agent Context Bundle\n")
    body.append("## Identity\n")
    body.append(f"- role: {prompt.stem}")
    body.append(f"- change: {change}")
    body.append(f"- prompt: {prompt}")
    body.append(f"- context_dir: {context_dir}")
    body.append(f"- change_dir: {change_dir / change}")
    body.append("")
    body.append("# Prompt\n")
    body.append(read_text(prompt).rstrip())
    body.append("")
    body.append("# Context\n")

    for path in context:
        body.append(file_section(context_dir, path))

    body.append("# Change\n")

    for path in change_file:
        body.append(file_section(change_dir / change, path))

    body.append("# Final Instruction\n")
    body.append("- Follow the prompt role.")
    body.append("- Obey context rules.")
    body.append("- Use the change artifact files as the source of task state.")
    body.append("- Do not invent missing approvals.")
    body.append("- Stop at the required handoff point.")
    body.append("")

    return "\n".join(body)


def manifest_text(
    bundle: Path,
    prompt: list[Path],
    context: list[Path],
    change_file: list[Path],
    change: str,
) -> str:
    body: list[str] = []

    body.append("# Agent Context Manifest\n")
    body.append("## Bundle\n")
    body.append(f"- bundle: {bundle}")
    body.append(f"- change: {change}")
    body.append("\n## Prompt\n")

    for path in prompt:
        body.append(f"- {path}")

    body.append("\n## Context\n")

    for path in context:
        body.append(f"- {path}")

    body.append("\n## Change\n")

    for path in change_file:
        body.append(f"- {path}")

    body.append("\n## Output\n")

    for path in sorted(bundle.glob("*.md")):
        body.append(f"- {path.name}")

    body.append("")
    return "\n".join(body)


def write_bundle(
    prompt_dir: Path,
    context_dir: Path,
    change_dir: Path,
    target: Path,
    change: str,
    bundle_id: str,
    logger: Any,
) -> list[Path]:
    prompt = prompt_list(prompt_dir)
    context = context_list(context_dir)
    change_file = change_list(change_dir, change)

    bundle = target / bundle_id

    if bundle.exists():
        raise FileExistsError(str(bundle))

    bundle.mkdir(parents=True, exist_ok=False)

    output: list[Path] = []

    for path in prompt:
        out = bundle / path.name
        text = bundle_text(
            prompt=path,
            prompt_dir=prompt_dir,
            context_dir=context_dir,
            change_dir=change_dir,
            change=change,
            context=context,
            change_file=change_file,
        )
        output.append(write_text(out, text))
        logger.info(jline("agent", "context", "write", {"path": str(out)}))

    manifest = bundle / "_manifest.md"
    output.append(write_text(manifest, manifest_text(bundle, prompt, context, change_file, change)))
    logger.info(jline("agent", "context", "write", {"path": str(manifest)}))

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
    if len(argv) != 7:
        raise ValueError("usage: write.py ROOT PROMPT_DIR CONTEXT_DIR CHANGE_DIR TARGET CHANGE")

    root = Path(argv[1]).resolve()
    prompt_dir = Path(argv[2])
    context_dir = Path(argv[3])
    change_dir = Path(argv[4])
    target = Path(argv[5])
    change = argv[6]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "prompt_dir": str(prompt_dir),
            "context_dir": str(context_dir),
            "change_dir": str(change_dir),
            "target": str(target),
            "change": change,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        bundle_id = Path(run.run_dir).name

        run.logger.info(
            jline(
                "script",
                "context",
                "start",
                {
                    "root": str(root),
                    "prompt_dir": str(prompt_dir),
                    "context_dir": str(context_dir),
                    "change_dir": str(change_dir),
                    "target": str(target),
                    "change": change,
                    "bundle": bundle_id,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_bundle(
            prompt_dir=prompt_dir,
            context_dir=context_dir,
            change_dir=change_dir,
            target=target,
            change=change,
            bundle_id=bundle_id,
            logger=run.logger,
        )

        run.logger.info(
            jline(
                "script",
                "context",
                "ok",
                {
                    "bundle": bundle_id,
                    "output": len(output),
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "bundle": bundle_id,
                "change": change,
                "target": str(target),
                "output": len(output),
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
    ) as error:
        fail(run, "context", error)


if __name__ == "__main__":
    main(sys.argv)
