from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
from research.util.git import git_commit, run_cmd
from research.util.jlog import jline
from research.util.run import Run, make_run, run_err, run_ok, task_name


def yaml_text(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def read_data(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    return data


def write_data(path: Path, data: dict[str, Any]) -> Path:
    return write_text(path, yaml_text(data))


def read_config(path: Path) -> dict[str, Any]:
    data = read_yaml(str(path))

    if not isinstance(data, dict):
        raise TypeError(str(path))

    if "agent" not in data:
        raise KeyError("agent")

    return data["agent"]


def latest_change(change_dir: Path, status: str) -> str:
    data: list[str] = []

    if not change_dir.is_dir():
        raise NotADirectoryError(str(change_dir))

    for path in sorted(change_dir.iterdir()):
        result = path / "result.yaml"

        if not result.is_file():
            continue

        item = read_data(result)

        if item["status"] == status:
            data.append(path.name)

    if not data:
        raise FileNotFoundError(f"{status} change not found")

    return data[-1]


def read_result(change_dir: Path, change: str) -> tuple[Path, dict[str, Any]]:
    path = change_dir / change / "result.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path, read_data(path)


def check_auto(config: dict[str, Any], data: dict[str, Any]) -> None:
    if config["mode"] != "auto":
        raise ValueError("agent mode is not auto")

    if data["status"] != "accepted":
        raise ValueError("auto requires accepted change")

    auto = config["auto"]
    risk = data["risk"]

    if risk not in auto["allow_risk"]:
        raise ValueError("risk is not allowed")

    if not auto["allow_rule_change"]:
        if str(data["title"]).lower().find("rule") >= 0:
            raise ValueError("rule change is not allowed")

    if not auto["allow_workflow_change"]:
        if str(data["title"]).lower().find("workflow") >= 0:
            raise ValueError("workflow change is not allowed")

    if not auto["allow_arch_change"]:
        if str(data["title"]).lower().find("architecture") >= 0:
            raise ValueError("architecture change is not allowed")


def apply_auto(
    root: Path,
    change_dir: Path,
    config_path: Path,
    change: str,
    run_dir: str,
) -> dict[str, Any]:
    if change == "latest":
        change = latest_change(change_dir, "accepted")

    config = read_config(config_path)
    path, data = read_result(change_dir, change)
    check_auto(config, data)

    fmt_out = run_cmd(root, ["just", "fmt"])
    check_out = run_cmd(root, ["just", "rule-check"])
    commit = git_commit(root, str(data["title"]))

    data["human"] = "auto"
    data["status"] = "committed"
    data["commit"] = commit
    data["decision_run"] = run_dir
    data["commit_run"] = run_dir
    data["check"] = {
        "fmt": "passed",
        "rule": "passed",
    }

    write_data(path, data)

    return {
        "change": change,
        "status": data["status"],
        "commit": commit,
        "fmt_output": fmt_out,
        "check_output": check_out,
    }


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
    if len(argv) != 5:
        raise ValueError("usage: auto.py ROOT CHANGE_DIR CONFIG CHANGE")

    root = Path(argv[1]).resolve()
    change_dir = Path(argv[2])
    config_path = Path(argv[3])
    change = argv[4]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "change_dir": str(change_dir),
            "config": str(config_path),
            "change": change,
        },
        script=script,
        src=root / "src",
        config=config_path,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "auto",
                "start",
                {
                    "root": str(root),
                    "change_dir": str(change_dir),
                    "config": str(config_path),
                    "change": change,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = apply_auto(root, change_dir, config_path, change, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "auto",
                "ok",
                {
                    "change": data["change"],
                    "status": data["status"],
                    "commit": data["commit"],
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "change": data["change"],
                "status": data["status"],
                "commit": data["commit"],
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
        subprocess.CalledProcessError,
    ) as error:
        fail(run, "auto", error)


if __name__ == "__main__":
    main(sys.argv)
