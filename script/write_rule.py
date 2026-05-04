from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress
from research.util.run import Run, make_run, run_err, run_ok


def read_index(root: Path, logger: Logger) -> dict[str, Any]:
    path = root / "rule" / "index.yaml"
    logger.info(jline("rule", "write", "read", {"path": str(path)}))
    return read_yaml(str(path))


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def make_page(name: str, data: Any) -> str:
    title = name.title()
    body = yaml_text(data)

    return f"""---
title: "{title}"
---

# {title}

```yaml
{body}```
"""


def make_word(root: Path, logger: Logger) -> str:
    body: list[str] = []
    word_dir = root / "rule" / "word"

    body.append('---\ntitle: "Word"\n---\n')
    body.append("# Word\n")

    for path in sorted(word_dir.glob("*.yaml")):
        item = read_yaml(str(path))
        logger.info(jline("rule", "write", "word", {"path": str(path)}))
        body.append(f"## {path.stem}\n")
        body.append("```yaml\n")
        body.append(yaml_text(item))
        body.append("```\n")

    return "\n".join(body)


def make_index(root: Path, logger: Logger) -> str:
    data = read_index(root, logger)
    body: list[str] = []

    body.append('---\ntitle: "Rule"\n---\n')
    body.append("# Rule\n")
    body.append("## Rule\n")

    for name in data["rule"]:
        title = name.title()
        body.append(f"- [{title}](./{name}.qmd)")

    body.append("\n## Word\n")
    body.append("- [Word](./word.qmd)")

    return "\n".join(body)


def make_context(root: Path, logger: Logger) -> str:
    data = read_index(root, logger)
    body: list[str] = []

    body.append("# Rule Context\n")

    for name in data["rule"]:
        path = root / "rule" / f"{name}.yaml"
        item = read_yaml(str(path))
        logger.info(jline("rule", "write", "context", {"path": str(path)}))
        body.append(f"## {name.title()}\n")
        body.append("```yaml\n")
        body.append(yaml_text(item))
        body.append("```\n")

    body.append("## Word\n")

    for name in data["word"]:
        path = root / "rule" / "word" / f"{name}.yaml"
        item = read_yaml(str(path))
        logger.info(jline("rule", "write", "context", {"path": str(path)}))
        body.append(f"### {name.title()}\n")
        body.append("```yaml\n")
        body.append(yaml_text(item))
        body.append("```\n")

    return "\n".join(body)


def write_rule(
    root: Path,
    doc_dir: Path,
    context_path: Path,
    logger: Logger,
) -> list[Path]:
    data = read_index(root, logger)
    output: list[Path] = []
    progress = make_progress(logger, "rule", len(data["rule"]) + 3)

    progress.start()

    for name in data["rule"]:
        path = root / "rule" / f"{name}.yaml"
        item = read_yaml(str(path))
        text = make_page(name, item)
        output_path = doc_dir / f"{name}.qmd"
        output.append(write_text(output_path, text))
        logger.info(jline("rule", "write", "page", {"path": str(output_path)}))
        progress.step(1)

    word_path = doc_dir / "word.qmd"
    output.append(write_text(word_path, make_word(root, logger)))
    logger.info(jline("rule", "write", "page", {"path": str(word_path)}))
    progress.step(1)

    index_path = doc_dir / "index.qmd"
    output.append(write_text(index_path, make_index(root, logger)))
    logger.info(jline("rule", "write", "page", {"path": str(index_path)}))
    progress.step(1)

    output.append(write_text(context_path, make_context(root, logger)))
    logger.info(jline("rule", "write", "context", {"path": str(context_path)}))
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
        raise ValueError("usage: write_rule.py ROOT DOC_DIR CONTEXT_PATH")

    root = Path(argv[1])
    doc_dir = Path(argv[2])
    context_path = Path(argv[3])
    run = make_run(
        root=root,
        name="write-rule",
        params={
            "task": "write-rule",
            "doc": str(doc_dir),
            "context": str(context_path),
        },
        script=root / "script" / "write_rule.py",
        src=root / "src",
        config=root / "rule" / "index.yaml",
    )

    try:
        run.logger.info(
            jline(
                "script",
                "rule",
                "start",
                {
                    "root": str(root),
                    "doc": str(doc_dir),
                    "context": str(context_path),
                    "run": run.run_dir,
                },
            )
        )

        output = write_rule(root, doc_dir, context_path, run.logger)

        run.logger.info(
            jline(
                "script",
                "rule",
                "ok",
                {
                    "output": len(output),
                    "run": run.run_dir,
                },
            )
        )
        run_ok(
            run,
            {
                "task": "write-rule",
                "output": len(output),
                "doc": str(doc_dir),
                "context": str(context_path),
            },
        )

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "rule", error)


if __name__ == "__main__":
    main(sys.argv)
