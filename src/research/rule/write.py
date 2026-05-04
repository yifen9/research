from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.rule.load import read_index


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


def make_word(root: Path) -> str:
    body: list[str] = []
    word_dir = root / "rule" / "word"

    body.append('---\ntitle: "Word"\n---\n')
    body.append("# Word\n")

    for path in sorted(word_dir.glob("*.yaml")):
        data = read_yaml(str(path))
        body.append(f"## {path.stem}\n")
        body.append("```yaml\n")
        body.append(yaml_text(data))
        body.append("```\n")

    return "\n".join(body)


def make_index(root: Path) -> str:
    data = read_index(root)
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


def make_context(root: Path) -> str:
    data = read_index(root)
    body: list[str] = []

    body.append("# Rule Context\n")

    for name in data["rule"]:
        path = root / "rule" / f"{name}.yaml"
        item = read_yaml(str(path))
        body.append(f"## {name.title()}\n")
        body.append("```yaml\n")
        body.append(yaml_text(item))
        body.append("```\n")

    body.append("## Word\n")

    for name in data["word"]:
        path = root / "rule" / "word" / f"{name}.yaml"
        item = read_yaml(str(path))
        body.append(f"### {name.title()}\n")
        body.append("```yaml\n")
        body.append(yaml_text(item))
        body.append("```\n")

    return "\n".join(body)


def write_rule(root: Path, doc_dir: Path, context_path: Path) -> list[Path]:
    data = read_index(root)
    output: list[Path] = []

    for name in data["rule"]:
        item = read_yaml(str(root / "rule" / f"{name}.yaml"))
        text = make_page(name, item)
        path = doc_dir / f"{name}.qmd"
        output.append(write_text(path, text))

    output.append(write_text(doc_dir / "word.qmd", make_word(root)))
    output.append(write_text(doc_dir / "index.qmd", make_index(root)))
    output.append(write_text(context_path, make_context(root)))

    return output
