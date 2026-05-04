from pathlib import Path
import sys
import yaml


def read_yaml(path):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def flat_yaml(data):
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    return text


def make_page(name, data):
    title = name.title()
    body = flat_yaml(data)
    text = f"""---
title: "{title}"
---

# {title}

```yaml
{body}```
"""
    return text


def make_word(root):
    word_dir = root / "rule" / "word"
    body = []
    body.append('---\ntitle: "Word"\n---\n')
    body.append("# Word\n")
    for path in sorted(word_dir.glob("*.yaml")):
        data = read_yaml(path)
        body.append(f"## {path.stem}\n")
        body.append("```yaml\n")
        body.append(flat_yaml(data))
        body.append("```\n")
    return "\n".join(body)


def make_index(root):
    data = read_yaml(root / "rule" / "index.yaml")
    body = []
    body.append('---\ntitle: "Rule"\n---\n')
    body.append("# Rule\n")
    body.append("## Rule\n")
    for name in data["rule"]:
        body.append(f"- [{name.title()}](./{name}.qmd)")
    body.append("\n## Word\n")
    body.append("- [Word](./word.qmd)")
    return "\n".join(body)


def make_context(root):
    data = read_yaml(root / "rule" / "index.yaml")
    body = []
    body.append("# Rule Context\n")
    for name in data["rule"]:
        path = root / "rule" / f"{name}.yaml"
        item = read_yaml(path)
        body.append(f"## {name.title()}\n")
        body.append("```yaml\n")
        body.append(flat_yaml(item))
        body.append("```\n")
    body.append("## Word\n")
    for name in data["word"]:
        path = root / "rule" / "word" / f"{name}.yaml"
        item = read_yaml(path)
        body.append(f"### {name.title()}\n")
        body.append("```yaml\n")
        body.append(flat_yaml(item))
        body.append("```\n")
    return "\n".join(body)


def main(argv):
    root = Path(argv[1])
    data = read_yaml(root / "rule" / "index.yaml")

    for name in data["rule"]:
        item = read_yaml(root / "rule" / f"{name}.yaml")
        text = make_page(name, item)
        write_text(root / "doc" / "rule" / f"{name}.qmd", text)

    write_text(root / "doc" / "rule" / "word.qmd", make_word(root))
    write_text(root / "doc" / "rule" / "index.qmd", make_index(root))
    write_text(root / "context" / "rule.md", make_context(root))


if __name__ == "__main__":
    main(sys.argv)
