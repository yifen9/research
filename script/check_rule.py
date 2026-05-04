from pathlib import Path
import ast
import re
import sys
import yaml


def read_yaml(path):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data


def load_word(root):
    pool = set()
    word_dir = root / "rule" / "word"
    for path in word_dir.glob("*.yaml"):
        data = read_yaml(path)
        for word in data["word"]:
            pool.add(word)
    return pool


def load_rule(root):
    data = {}
    for path in (root / "rule").glob("*.yaml"):
        data[path.stem] = read_yaml(path)
    return data


def split_name(name):
    name = name.replace("-", "_")
    part = [x for x in name.split("_") if x]
    return part


def good_word(name, pool):
    part = split_name(name)
    if len(part) > 2:
        return False
    for item in part:
        if item not in pool:
            return False
    return True


def good_kebab(name):
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) is not None


def good_snake(name):
    return re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", name) is not None


def skip_path(path):
    skip = {".git", ".quarto", "__pycache__", ".venv", "build"}
    for part in path.parts:
        if part in skip:
            return True
    return False


def check_line(path, rule):
    max_line = rule["code"]["file"]["max_line"]
    size = len(path.read_text(encoding="utf-8").splitlines())
    if size > max_line:
        return [(path, 0, str(size), "line")]
    return []


def nest_depth(node, depth):
    target = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.Match,
    )
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, target):
            best = max(best, nest_depth(child, depth + 1))
        else:
            best = max(best, nest_depth(child, depth))
    return best


def check_code(path, pool, rule):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = []
    max_nest = rule["code"]["nest"]["max"]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if len(node.args.defaults) > 0:
                bad.append((path, node.lineno, node.name, "default"))
            if len(node.args.kw_defaults) > 0:
                for item in node.args.kw_defaults:
                    if item is not None:
                        bad.append((path, node.lineno, node.name, "default"))
            if not good_word(node.name, pool):
                bad.append((path, node.lineno, node.name, "name"))
            if nest_depth(node, 0) > max_nest:
                bad.append((path, node.lineno, node.name, "nest"))

        if isinstance(node, ast.AsyncFunctionDef):
            if len(node.args.defaults) > 0:
                bad.append((path, node.lineno, node.name, "default"))
            if len(node.args.kw_defaults) > 0:
                for item in node.args.kw_defaults:
                    if item is not None:
                        bad.append((path, node.lineno, node.name, "default"))
            if not good_word(node.name, pool):
                bad.append((path, node.lineno, node.name, "name"))
            if nest_depth(node, 0) > max_nest:
                bad.append((path, node.lineno, node.name, "nest"))

        if isinstance(node, ast.Name):
            if not good_word(node.id, pool):
                bad.append((path, node.lineno, node.id, "name"))

    return bad


def check_dir(path, pool, rule):
    bad = []
    deny = set(rule["file"]["deny"])
    allow = set(rule["name"]["allow"])

    for part in path.parts:
        if part in deny:
            bad.append((path, 0, part, "deny"))
        if part in allow:
            continue
        if part.startswith("."):
            continue
        if not good_kebab(part):
            bad.append((path, 0, part, "case"))
        if not good_word(part, pool):
            bad.append((path, 0, part, "word"))

    return bad


def check_file(path, pool, rule):
    bad = []
    allow = set(rule["name"]["allow"])
    stem = path.stem
    name = path.name

    if name in allow:
        return bad

    if path.suffix == ".py":
        if not good_snake(stem):
            bad.append((path, 0, stem, "case"))
        if not good_word(stem, pool):
            bad.append((path, 0, stem, "word"))
        return bad

    if path.suffix in {".yaml", ".yml", ".toml", ".json", ".qmd", ".md"}:
        if not good_kebab(stem):
            bad.append((path, 0, stem, "case"))
        if not good_word(stem, pool):
            bad.append((path, 0, stem, "word"))
        return bad

    return bad


def check_conf(path):
    bad = []

    if path.suffix == ".yml":
        bad.append((path, 0, path.name, "yaml"))

    if path.suffix == ".json":
        allow = {"package.json", "tsconfig.json", "devcontainer.json"}
        if path.name not in allow:
            bad.append((path, 0, path.name, "json"))

    return bad


def scan_file(root, pool, rule):
    bad = []

    for path in root.rglob("*"):
        if skip_path(path):
            continue

        rel = path.relative_to(root)

        if path.is_dir():
            bad.extend(check_dir(rel, pool, rule))
            continue

        bad.extend(check_file(rel, pool, rule))
        bad.extend(check_conf(rel))

        if path.suffix == ".py":
            bad.extend(check_line(path, rule["code"]))
            bad.extend(check_code(path, pool, rule["code"]))

    return bad


def main(argv):
    root = Path(argv[1])
    pool = load_word(root)
    rule = load_rule(root)
    bad = scan_file(root, pool, rule)

    for path, line, name, kind in bad:
        print(f"{path}:{line}: {kind}: {name}")

    if bad:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
