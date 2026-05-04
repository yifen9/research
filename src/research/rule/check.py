from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from research.io.text import read_text
from research.rule.load import load_rule, load_word
from research.rule.name import good_kebab, good_snake, good_word


Bad = tuple[Path, int, str, str]


def skip_path(path: Path) -> bool:
    skip = {".git", ".quarto", "__pycache__", ".venv", "build"}

    for part in path.parts:
        if part in skip:
            return True

    return False


def check_line(path: Path, rule: dict[str, Any]) -> list[Bad]:
    max_line = rule["code"]["file"]["max_line"]
    size = len(read_text(path).splitlines())

    if size > max_line:
        return [(path, 0, str(size), "line")]

    return []


def nest_depth(node: ast.AST, depth: int) -> int:
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


def check_arg(arg: ast.arguments, pool: set[str], path: Path, line: int) -> list[Bad]:
    bad: list[Bad] = []

    for item in arg.posonlyargs:
        if not good_word(item.arg, pool):
            bad.append((path, line, item.arg, "arg"))

    for item in arg.args:
        if not good_word(item.arg, pool):
            bad.append((path, line, item.arg, "arg"))

    for item in arg.kwonlyargs:
        if not good_word(item.arg, pool):
            bad.append((path, line, item.arg, "arg"))

    if arg.vararg is not None and not good_word(arg.vararg.arg, pool):
        bad.append((path, line, arg.vararg.arg, "arg"))

    if arg.kwarg is not None and not good_word(arg.kwarg.arg, pool):
        bad.append((path, line, arg.kwarg.arg, "arg"))

    return bad


def check_default(arg: ast.arguments, path: Path, line: int, name: str) -> list[Bad]:
    bad: list[Bad] = []

    if len(arg.defaults) > 0:
        bad.append((path, line, name, "default"))

    for item in arg.kw_defaults:
        if item is not None:
            bad.append((path, line, name, "default"))

    return bad


def target_name(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]

    if isinstance(node, ast.Tuple):
        data: list[str] = []
        for item in node.elts:
            data.extend(target_name(item))
        return data

    if isinstance(node, ast.List):
        data: list[str] = []
        for item in node.elts:
            data.extend(target_name(item))
        return data

    return []


def check_target(node: ast.AST, pool: set[str], path: Path, line: int) -> list[Bad]:
    bad: list[Bad] = []

    for name in target_name(node):
        if not good_word(name, pool):
            bad.append((path, line, name, "name"))

    return bad


def check_try(node: ast.Try, path: Path) -> list[Bad]:
    bad: list[Bad] = []

    for item in node.handlers:
        if item.type is None:
            bad.append((path, item.lineno, "except", "fallback"))
            continue

        if isinstance(item.type, ast.Name):
            if item.type.id in {"Exception", "BaseException"}:
                bad.append((path, item.lineno, item.type.id, "fallback"))

        if len(item.body) == 1 and isinstance(item.body[0], ast.Pass):
            bad.append((path, item.lineno, "pass", "fallback"))

    return bad


def check_func(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    pool: set[str],
    path: Path,
    rule: dict[str, Any],
) -> list[Bad]:
    bad: list[Bad] = []
    max_nest = rule["code"]["nest"]["max"]

    bad.extend(check_default(node.args, path, node.lineno, node.name))
    bad.extend(check_arg(node.args, pool, path, node.lineno))

    if not good_word(node.name, pool):
        bad.append((path, node.lineno, node.name, "name"))

    if nest_depth(node, 0) > max_nest:
        bad.append((path, node.lineno, node.name, "nest"))

    return bad


def check_code(path: Path, pool: set[str], rule: dict[str, Any]) -> list[Bad]:
    tree = ast.parse(read_text(path))
    bad: list[Bad] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            bad.extend(check_func(node, pool, path, rule))

        if isinstance(node, ast.AsyncFunctionDef):
            bad.extend(check_func(node, pool, path, rule))

        if isinstance(node, ast.Assign):
            for item in node.targets:
                bad.extend(check_target(item, pool, path, node.lineno))

        if isinstance(node, ast.AnnAssign):
            bad.extend(check_target(node.target, pool, path, node.lineno))

        if isinstance(node, ast.For):
            bad.extend(check_target(node.target, pool, path, node.lineno))

        if isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars is not None:
                    bad.extend(
                        check_target(item.optional_vars, pool, path, node.lineno)
                    )

        if isinstance(node, ast.Try):
            bad.extend(check_try(node, path))

    return bad


def check_dir(path: Path, pool: set[str], rule: dict[str, Any]) -> list[Bad]:
    bad: list[Bad] = []
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


def check_file(path: Path, pool: set[str], rule: dict[str, Any]) -> list[Bad]:
    bad: list[Bad] = []
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


def check_conf(path: Path, rule: dict[str, Any]) -> list[Bad]:
    bad: list[Bad] = []

    if path.suffix == ".yml":
        bad.append((path, 0, path.name, "yaml"))

    if path.suffix == ".json":
        allow = set(rule["config"]["json"]["allow"])

        if path.name not in allow:
            bad.append((path, 0, path.name, "json"))

    return bad


def scan_file(root: Path, pool: set[str], rule: dict[str, Any]) -> list[Bad]:
    bad: list[Bad] = []

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


def check_root(root: Path) -> list[Bad]:
    pool = load_word(root)
    rule = load_rule(root)
    return scan_file(root, pool, rule)


def print_bad(bad: list[Bad]) -> None:
    for path, line, name, kind in bad:
        print(f"{path}:{line}: {kind}: {name}")
