from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

from research.io.text import write_text
from research.io.yaml import read_yaml
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


def check_decide(decision: str) -> None:
    allow = {"approve", "return", "discard"}

    if decision not in allow:
        raise ValueError(f"invalid decision: {decision}")


def next_status(decision: str) -> str:
    if decision == "approve":
        return "approved"

    if decision == "return":
        return "returned"

    if decision == "discard":
        return "discarded"

    raise ValueError(f"invalid decision: {decision}")


def read_result(change_dir: Path, change: str) -> tuple[Path, dict[str, Any]]:
    path = change_dir / change / "result.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return path, read_data(path)


def check_state(data: dict[str, Any], decision: str) -> None:
    status = data["status"]

    if decision == "approve" and status != "accepted":
        raise ValueError("approve requires accepted change")

    if decision == "return" and status not in {"accepted", "rejected"}:
        raise ValueError("return requires accepted or rejected change")

    if decision == "discard" and status not in {
        "draft",
        "accepted",
        "rejected",
        "returned",
    }:
        raise ValueError(
            "discard requires draft, accepted, rejected, or returned change"
        )


def apply_decide(
    change_dir: Path,
    change: str,
    decision: str,
    run_dir: str,
) -> dict[str, Any]:
    check_decide(decision)
    path, data = read_result(change_dir, change)
    check_state(data, decision)

    data["human"] = decision
    data["status"] = next_status(decision)
    data["decision_run"] = run_dir

    write_data(path, data)
    return data


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
        raise ValueError("usage: decide.py ROOT CHANGE_DIR CHANGE DECISION")

    root = Path(argv[1]).resolve()
    change_dir = Path(argv[2])
    change = argv[3]
    decision = argv[4]
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "change_dir": str(change_dir),
            "change": change,
            "decision": decision,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "decide",
                "start",
                {
                    "root": str(root),
                    "change_dir": str(change_dir),
                    "change": change,
                    "decision": decision,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = apply_decide(change_dir, change, decision, run.run_dir)

        run.logger.info(
            jline(
                "script",
                "decide",
                "ok",
                {
                    "change": change,
                    "status": data["status"],
                    "decision": decision,
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "change": change,
                "decision": decision,
                "status": data["status"],
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
        fail(run, "decide", error)


if __name__ == "__main__":
    main(sys.argv)
