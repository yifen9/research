from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
from typing import Any

from research.io.text import read_text
from research.io.yaml import read_yaml
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress
from research.util.run import Run, make_run, run_err, run_ok, task_name


def read_index(root: Path) -> dict[str, Any]:
    path = rule_root(root) / "index.yaml"
    data = read_yaml(str(path))

    if "rule" not in data:
        raise KeyError("rule")

    if "word" not in data:
        raise KeyError("word")

    return data


def rule_root(root: Path) -> Path:
    return root / "config" / "rule"


def load_rule(root: Path, logger: Logger) -> dict[str, Any]:
    data: dict[str, Any] = {}
    index = read_index(root)

    for name in index["rule"]:
        path = rule_root(root) / f"{name}.yaml"
        logger.info(jline("rule", "check", "load", {"path": str(path)}))
        item = read_yaml(str(path))

        if name not in item:
            logger.error(
                jline(
                    "rule",
                    "check",
                    "miss",
                    {
                        "path": str(path),
                        "key": name,
                    },
                )
            )
            raise KeyError(name)

        data[name] = item[name]

    return data


def load_word(root: Path, logger: Logger) -> set[str]:
    pool: set[str] = set()
    index = read_index(root)

    for name in index["word"]:
        path = rule_root(root) / "word" / f"{name}.yaml"
        logger.info(jline("rule", "check", "word", {"path": str(path)}))
        data = read_yaml(str(path))

        if "word" not in data:
            raise KeyError("word")

        for word in data["word"]:
            pool.add(word)

    return pool


def split_name(name: str) -> list[str]:
    text = name.replace("-", "_")
    return [item for item in text.split("_") if item]


def good_word(name: str, pool: set[str]) -> bool:
    part = split_name(name)

    if len(part) > 2:
        return False

    if len(part) == 2 and part[1].isdigit():
        return part[0] in pool

    for item in part:
        if item not in pool:
            return False

    return True


def py_word(name: str, pool: set[str]) -> bool:
    if name in {"self", "cls"}:
        return True

    if name.startswith("__") and name.endswith("__"):
        return True

    if name.isupper():
        return True

    if name[:1].isupper():
        return True

    return good_word(name, pool)


def good_kebab(name: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) is not None


def good_snake(name: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", name) is not None


def skip_path(path: Path) -> bool:
    skip = {
        ".git",
        ".cache",
        ".github",
        ".opencode",
        ".quarto",
        ".ruff_cache",
        ".sisyphus",
        ".venv",
        "__pycache__",
        "_extensions",
        "build",
        "out",
    }

    part = path.parts

    if len(part) > 3 and part[0] == "project" and part[2] == "proposal" and part[3] == "version":
        return True

    if len(part) > 2 and part[0] == "project" and part[2] == "repo":
        return True

    if len(part) > 1 and part[0] == "agent" and part[1] == "context":
        return True

    if part and part[0] == "context":
        return True

    for item in part:
        if item in skip:
            return True

        if item.endswith(".egg-info"):
            return True

    return False


def check_line(path: Path, rule: dict[str, Any]) -> list[tuple[Path, int, str, str]]:
    max_line = rule["file"]["max_line"]
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


def check_arg(
    arg: ast.arguments,
    pool: set[str],
    path: Path,
    line: int,
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []

    for item in arg.posonlyargs:
        if not py_word(item.arg, pool):
            bad.append((path, line, item.arg, "arg"))

    for item in arg.args:
        if not py_word(item.arg, pool):
            bad.append((path, line, item.arg, "arg"))

    for item in arg.kwonlyargs:
        if not py_word(item.arg, pool):
            bad.append((path, line, item.arg, "arg"))

    if arg.vararg is not None:
        if not py_word(arg.vararg.arg, pool):
            bad.append((path, line, arg.vararg.arg, "arg"))

    if arg.kwarg is not None:
        if not py_word(arg.kwarg.arg, pool):
            bad.append((path, line, arg.kwarg.arg, "arg"))

    return bad


def check_default(
    arg: ast.arguments,
    path: Path,
    line: int,
    name: str,
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []

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


def check_target(
    node: ast.AST,
    pool: set[str],
    path: Path,
    line: int,
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []

    for name in target_name(node):
        if not py_word(name, pool):
            bad.append((path, line, name, "name"))

    return bad


def check_try(node: ast.Try, path: Path) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []

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
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []
    max_nest = rule["nest"]["max"]

    bad.extend(check_default(node.args, path, node.lineno, node.name))
    bad.extend(check_arg(node.args, pool, path, node.lineno))

    if not py_word(node.name, pool):
        bad.append((path, node.lineno, node.name, "name"))

    if nest_depth(node, 0) > max_nest:
        bad.append((path, node.lineno, node.name, "nest"))

    return bad


def check_code(
    path: Path,
    pool: set[str],
    rule: dict[str, Any],
) -> list[tuple[Path, int, str, str]]:
    tree = ast.parse(read_text(path))
    bad: list[tuple[Path, int, str, str]] = []

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


def check_dir(
    path: Path,
    pool: set[str],
    rule: dict[str, Any],
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []
    deny_set = set(rule["file"]["deny"])
    allow = set(rule["name"]["allow"])

    for index, part in enumerate(path.parts):
        if part in deny_set:
            bad.append((path, 0, part, "deny"))

        if part in allow:
            continue

        if index == 1 and path.parts[0] == "project":
            if not good_kebab(part):
                bad.append((path, 0, part, "case"))
            continue

        if part.startswith("."):
            continue

        if not good_kebab(part):
            bad.append((path, 0, part, "case"))

        if not good_word(part, pool):
            bad.append((path, 0, part, "word"))

    return bad


def check_file(
    path: Path,
    pool: set[str],
    rule: dict[str, Any],
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []
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


def check_conf(path: Path, rule: dict[str, Any]) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []

    if path.suffix == ".yml":
        bad.append((path, 0, path.name, "yaml"))

    if path.suffix == ".json":
        allow = set(rule["config"]["json"]["allow"])

        if path.name not in allow:
            bad.append((path, 0, path.name, "json"))

    return bad


def check_agent(root: Path) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []
    conf_path = root / "config" / "agent.yaml"
    conf_rel = Path("config/agent.yaml")

    if not conf_path.is_file():
        return [(conf_rel, 0, "agent", "miss")]

    conf = read_yaml(str(conf_path))
    backend = conf.get("backend", {})
    session = conf.get("session", {})
    vector = session.get("vector", {})

    active = backend.get("active")
    if not isinstance(active, str):
        bad.append((conf_rel, 2, str(active), "active"))
    elif not (root / "agent" / "backend" / active / "manifest.yaml").is_file():
        bad.append((conf_rel, 2, active, "active"))

    if vector.get("required") is not True:
        bad.append((conf_rel, 12, str(vector.get("required")), "required"))

    if vector.get("failure") != "fail":
        bad.append((conf_rel, 9, str(vector.get("failure")), "fail"))

    if not vector.get("backend"):
        bad.append((conf_rel, 7, "backend", "miss"))

    role_dir = root / "agent" / "workflow" / "role"
    role_data = [path.stem for path in role_dir.glob("*.md")]

    if "architect" not in role_data:
        bad.append((Path("agent/workflow/role"), 0, "architect", "miss"))

    for name in role_data:
        if name != "architect":
            bad.append((Path("agent/workflow/role") / f"{name}.md", 0, name, "role"))

    path = root / "agent" / "workflow" / "session" / "architect.md"
    rel = Path("agent/workflow/session/architect.md")

    if path.is_file():
        text = read_text(path)
        for item in ["config/rule/", "config/agent.yaml", "vector backend is required"]:
            if item not in text:
                bad.append((rel, 0, item, "context"))
    else:
        bad.append((rel, 0, "architect", "miss"))

    path = root / ".gitignore"
    rel = Path(".gitignore")

    if path.is_file():
        text = read_text(path)
        for item in ["/opencode.json", "/out"]:
            if item not in text:
                bad.append((rel, 0, item, "gitignore"))
    else:
        bad.append((rel, 0, "gitignore", "miss"))

    index = read_index(root)
    if index.get("word") != ["core"]:
        bad.append((Path("config/rule/index.yaml"), 9, "word", "core"))

    if (root / "rule").exists():
        bad.append((Path("rule"), 0, "rule", "root"))

    if (root / "template").exists():
        bad.append((Path("template"), 0, "template", "root"))

    for item in ["_quarto.yaml", "index.qmd", "styles.css", "theme.scss", "favicon.png", "_extensions"]:
        if (root / item).exists():
            bad.append((Path(item), 0, item, "root"))

    if not (root / "doc" / "_quarto.yaml").is_file():
        bad.append((Path("doc/_quarto.yaml"), 0, "doc", "miss"))

    return bad


def check_top(root: Path, rule: dict[str, Any]) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []
    allow = set(rule["file"]["root"])

    for path in root.iterdir():
        if not path.is_dir():
            continue

        name = path.name
        if name.startswith(".") or name in {"out", "build", "__pycache__"}:
            continue

        if name not in allow:
            bad.append((Path(name), 0, name, "root"))

    return bad


def path_list(root: Path) -> list[Path]:
    data: list[Path] = []

    for path in root.rglob("*"):
        rel = path.relative_to(root)

        if not skip_path(rel):
            data.append(path)

    return data


def scan_file(
    root: Path,
    pool: set[str],
    rule: dict[str, Any],
    logger: Logger,
) -> list[tuple[Path, int, str, str]]:
    bad: list[tuple[Path, int, str, str]] = []
    data = path_list(root)
    progress = make_progress(logger, "check", len(data))
    progress.start()

    for path in data:
        rel = path.relative_to(root)

        if path.is_dir():
            bad.extend(check_dir(rel, pool, rule))
            progress.step(1)
            continue

        bad.extend(check_file(rel, pool, rule))
        bad.extend(check_conf(rel, rule))

        if path.suffix == ".py":
            bad.extend(check_line(path, rule["code"]))
            bad.extend(check_code(path, pool, rule["code"]))

        progress.step(1)

    progress.finish()
    return bad


def check_root(root: Path, logger: Logger) -> list[tuple[Path, int, str, str]]:
    logger.info(jline("rule", "check", "load", {"root": str(root)}))
    pool = load_word(root, logger)
    rule = load_rule(root, logger)
    logger.info(jline("rule", "check", "scan", {"root": str(root)}))
    bad = scan_file(root, pool, rule, logger)
    bad.extend(check_top(root, rule))
    bad.extend(check_agent(root))
    return bad


def bad_item(item: tuple[Path, int, str, str]) -> dict[str, Any]:
    path, line, name, kind = item

    return {
        "path": str(path),
        "line": line,
        "name": name,
        "kind": kind,
    }


def count_key(data: list[dict[str, Any]], key: str) -> dict[str, int]:
    output: dict[str, int] = {}

    for item in data:
        value = str(item[key])
        if value not in output:
            output[value] = 0
        output[value] += 1

    return dict(sorted(output.items(), key=lambda item: item[1], reverse=True))


def bad_data(bad: list[tuple[Path, int, str, str]], task: str) -> dict[str, Any]:
    data = [bad_item(item) for item in bad]

    return {
        "task": task,
        "bad_count": len(data),
        "stat": {
            "total": len(data),
        },
        "top_kind": count_key(data, "kind"),
        "top_path": count_key(data, "path"),
        "bad": data,
        "next": [
            "Fix rule violations listed in the Violation section.",
            "Prefer renaming code to existing words before extending config/rule/word/core.yaml.",
            "Only add new words when the existing dictionary cannot express the intended meaning.",
            "Rerun just rule-check after changes.",
        ],
    }


def print_bad(bad: list[tuple[Path, int, str, str]], logger: Logger) -> None:
    for path, line, name, kind in bad:
        logger.error(
            jline(
                "rule",
                "check",
                "bad",
                {
                    "path": str(path),
                    "line": line,
                    "name": name,
                    "kind": kind,
                },
            )
        )


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
    if len(argv) != 2:
        raise ValueError("usage: check.py ROOT")

    root = Path(argv[1]).resolve()
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={"task": task},
        script=script,
        src=root / "src",
        config=root / "config" / "rule" / "index.yaml",
    )

    try:
        run.logger.info(
            jline(
                "script",
                "check",
                "start",
                {
                    "root": str(root),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        bad = check_root(root, run.logger)
        print_bad(bad, run.logger)

        if bad:
            error = RuntimeError("rule check failed")
            data = bad_data(bad, task)
            run.logger.error(
                jline(
                    "script",
                    "check",
                    "fail",
                    {
                        "bad": len(bad),
                        "run": run.run_dir,
                        "summary": str(run.summary_path),
                    },
                )
            )
            run_err(run, error, data)
            sys.exit(1)

        run.logger.info(
            jline(
                "script",
                "check",
                "ok",
                {
                    "bad": 0,
                    "run": run.run_dir,
                },
            )
        )
        run_ok(
            run,
            {
                "task": task,
                "bad_count": 0,
                "stat": {
                    "total": 0,
                },
                "next": [
                    "No rule violation found.",
                ],
            },
        )
        sys.exit(0)

    except (ValueError, KeyError, FileNotFoundError, RuntimeError, TypeError) as error:
        fail(run, "check", error)


if __name__ == "__main__":
    main(sys.argv)
