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
from research.util.run import Run, make_run, run_err, run_ok, task_name


def read_index(rule_dir: Path, logger: Logger) -> dict[str, Any]:
    path = rule_dir / "index.yaml"
    logger.info(jline("context", "rule", "read", {"path": str(path)}))
    data = read_yaml(str(path))

    if "rule" not in data:
        raise KeyError("rule")

    if "word" not in data:
        raise KeyError("word")

    return data


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def title_text(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def rule_path(rule_dir: Path, name: str) -> Path:
    return rule_dir / f"{name}.yaml"


def word_path(rule_dir: Path, name: str) -> Path:
    return rule_dir / "word" / f"{name}.yaml"


def read_rule(rule_dir: Path, name: str, logger: Logger) -> dict[str, Any]:
    path = rule_path(rule_dir, name)
    logger.info(jline("context", "rule", "read", {"path": str(path)}))
    data = read_yaml(str(path))

    if name not in data:
        raise KeyError(name)

    return data


def read_word(rule_dir: Path, name: str, logger: Logger) -> dict[str, Any]:
    path = word_path(rule_dir, name)
    logger.info(jline("context", "rule", "read", {"path": str(path)}))
    data = read_yaml(str(path))

    if "word" not in data:
        raise KeyError("word")

    return data


def make_page(name: str, data: dict[str, Any]) -> str:
    title = title_text(name)
    body = yaml_text(data)

    return f"""# {title}

## Source

- source: rule/{name}.yaml

## Content

```yaml
{body}```
"""


def make_word(rule_dir: Path, index: dict[str, Any], logger: Logger) -> str:
    body: list[str] = []

    body.append("# Word\n")
    body.append("## Source\n")
    body.append("- source: rule/word/*.yaml\n")
    body.append("## Content\n")

    for name in index["word"]:
        data = read_word(rule_dir, name, logger)
        body.append(f"### {title_text(name)}\n")
        body.append("```yaml")
        body.append(yaml_text(data).rstrip())
        body.append("```\n")

    return "\n".join(body)


def make_manifest(rule_dir: Path, target: Path, index: dict[str, Any]) -> str:
    body: list[str] = []

    body.append("# Rule Manifest\n")
    body.append("## Purpose\n")
    body.append(
        "This directory contains agent-readable rule documents generated from rule YAML files.\n"
    )
    body.append("## Source\n")
    body.append(f"- rule_dir: {rule_dir}")
    body.append(f"- target: {target}")
    body.append("\n## Read Order\n")

    for name in index["rule"]:
        body.append(f"- [{title_text(name)}](./{name}.md)")

    body.append("- [Word](./word.md)")
    body.append("\n## Rule\n")
    body.append("- YAML files under rule/ are the source of truth.")
    body.append("- Markdown files under context/rule/ are generated.")
    body.append("- Do not edit context/rule/*.md manually.")
    body.append("- Update rule/*.yaml first, then rerun context-rule-write.")
    body.append("")

    return "\n".join(body)


def clean_target(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)

    for path in target.glob("*.md"):
        path.unlink()


def write_rule(root: Path, rule_dir: Path, target: Path, logger: Logger) -> list[Path]:
    index = read_index(rule_dir, logger)
    output: list[Path] = []
    total = len(index["rule"]) + 2
    progress = make_progress(logger, "context-rule", total)

    clean_target(target)
    progress.start()

    for name in index["rule"]:
        data = read_rule(rule_dir, name, logger)
        text = make_page(name, data)
        path = target / f"{name}.md"
        output.append(write_text(path, text))
        logger.info(jline("context", "rule", "write", {"path": str(path)}))
        progress.step(1)

    word = make_word(rule_dir, index, logger)
    word_out = target / "word.md"
    output.append(write_text(word_out, word))
    logger.info(jline("context", "rule", "write", {"path": str(word_out)}))
    progress.step(1)

    manifest = make_manifest(rule_dir, target, index)
    manifest_out = target / "_manifest.md"
    output.append(write_text(manifest_out, manifest))
    logger.info(jline("context", "rule", "write", {"path": str(manifest_out)}))
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
        raise ValueError("usage: write.py ROOT RULE_DIR TARGET")

    root = Path(argv[1]).resolve()
    rule_dir = Path(argv[2])
    target = Path(argv[3])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "rule_dir": str(rule_dir),
            "target": str(target),
        },
        script=script,
        src=root / "src",
        config=rule_dir / "index.yaml",
    )

    try:
        run.logger.info(
            jline(
                "script",
                "rule",
                "start",
                {
                    "root": str(root),
                    "rule_dir": str(rule_dir),
                    "target": str(target),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_rule(root, rule_dir, target, run.logger)

        run.logger.info(
            jline(
                "script",
                "rule",
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
                "rule_dir": str(rule_dir),
                "target": str(target),
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
        fail(run, "rule", error)


if __name__ == "__main__":
    main(sys.argv)
