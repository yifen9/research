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


def check_status(status: str) -> None:
    allow = {"accept", "reject"}

    if status not in allow:
        raise ValueError(f"invalid status: {status}")


def check_risk(risk: str) -> None:
    allow = {"low", "medium", "high"}

    if risk not in allow:
        raise ValueError(f"invalid risk: {risk}")


def result_status(status: str) -> str:
    if status == "accept":
        return "accepted"

    if status == "reject":
        return "rejected"

    raise ValueError(f"invalid status: {status}")


def state_path(session_dir: Path, session: str) -> Path:
    return session_dir / session / "state.yaml"


def read_state(session_dir: Path, session: str) -> dict[str, Any]:
    path = state_path(session_dir, session)

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return read_data(path)


def check_role(data: dict[str, Any], role: str) -> None:
    if data["role"] != role:
        raise ValueError(f"session is not {role}")


def check_live(data: dict[str, Any]) -> None:
    if data["status"] == "retired":
        raise ValueError("session is retired")


def pass_rate(data: dict[str, Any]) -> float | None:
    task_count = int(data["task_count"])

    if task_count == 0:
        return None

    accept_count = int(data["accept_count"])
    return accept_count / task_count


def update_worker(data: dict[str, Any], status: str) -> dict[str, Any]:
    data["task_count"] = int(data["task_count"]) + 1

    if status == "accept":
        data["accept_count"] = int(data["accept_count"]) + 1

    if status == "reject":
        data["reject_count"] = int(data["reject_count"]) + 1

    data["pass_rate"] = pass_rate(data)

    threshold = float(data["threshold"])
    task_count = int(data["task_count"])

    if (
        task_count >= 6
        and data["pass_rate"] is not None
        and data["pass_rate"] < threshold
    ):
        data["status"] = "retired"
    else:
        data["status"] = "active"

    return data


def update_summary(session_dir: Path, session: str, data: dict[str, Any]) -> Path:
    body: list[str] = []

    body.append("# Session Summary\n")
    body.append("## Status\n")
    body.append(f"- session: {data['session']}")
    body.append(f"- role: {data['role']}")
    body.append(f"- status: {data['status']}")
    body.append(f"- threshold: {data['threshold']}")
    body.append(f"- task_count: {data['task_count']}")
    body.append(f"- accept_count: {data['accept_count']}")
    body.append(f"- reject_count: {data['reject_count']}")
    body.append(f"- pass_rate: {data['pass_rate']}")
    body.append(f"- created_run: {data['created_run']}")
    body.append("\n## File\n")
    body.append("- state: state.yaml")
    body.append("- memory: memory.md")
    body.append("")

    path = session_dir / session / "_summary.md"
    return write_text(path, "\n".join(body))


def read_result(change_dir: Path, change: str) -> dict[str, Any]:
    path = change_dir / change / "result.yaml"

    if not path.is_file():
        raise FileNotFoundError(str(path))

    return read_data(path)


def update_result(
    change_dir: Path,
    change: str,
    result: dict[str, Any],
    reviewer: str,
    status: str,
    risk: str,
    run_dir: str,
) -> dict[str, Any]:
    if result["status"] not in {"draft", "rejected", "accepted"}:
        raise ValueError(f"invalid change state: {result['status']}")

    result["status"] = result_status(status)
    result["reviewer"] = reviewer
    result["risk"] = risk
    result["review_run"] = run_dir

    path = change_dir / change / "result.yaml"
    write_data(path, result)

    return result


def write_review_note(
    change_dir: Path,
    change: str,
    reviewer: str,
    status: str,
    risk: str,
    run_dir: str,
) -> Path:
    path = change_dir / change / "review.md"

    body: list[str] = []
    body.append("# Review\n")
    body.append("## Change\n")
    body.append(f"- id: {change}")
    body.append(f"- reviewer: {reviewer}")
    body.append(f"- review_run: {run_dir}")
    body.append("\n## Status\n")
    body.append(status)
    body.append("\n## Risk\n")
    body.append(risk)
    body.append("\n## Reason\n")
    body.append("To be filled by the reviewer.")
    body.append("\n## Checked File\n")
    body.append("- To be filled by the reviewer.")
    body.append("\n## Checked Command\n")
    body.append("- To be filled by the reviewer.")
    body.append("\n## Required Change\n")
    body.append("- To be filled by the reviewer.")
    body.append("\n## Recommendation\n")
    body.append("To be filled by the reviewer.")
    body.append("")

    return write_text(path, "\n".join(body))


def apply_review(
    change_dir: Path,
    session_dir: Path,
    change: str,
    reviewer: str,
    status: str,
    risk: str,
    run_dir: str,
) -> dict[str, Any]:
    check_status(status)
    check_risk(risk)

    result = read_result(change_dir, change)
    worker = result["worker"]

    worker_state = read_state(session_dir, worker)
    reviewer_state = read_state(session_dir, reviewer)

    check_role(worker_state, "worker")
    check_role(reviewer_state, "reviewer")
    check_live(worker_state)
    check_live(reviewer_state)

    result = update_result(change_dir, change, result, reviewer, status, risk, run_dir)

    worker_state = update_worker(worker_state, status)
    write_data(state_path(session_dir, worker), worker_state)
    update_summary(session_dir, worker, worker_state)

    write_review_note(change_dir, change, reviewer, status, risk, run_dir)

    return {
        "change": change,
        "worker": worker,
        "reviewer": reviewer,
        "status": result["status"],
        "risk": risk,
        "worker_status": worker_state["status"],
        "task_count": worker_state["task_count"],
        "accept_count": worker_state["accept_count"],
        "reject_count": worker_state["reject_count"],
        "pass_rate": worker_state["pass_rate"],
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
    if len(argv) != 8:
        raise ValueError(
            "usage: review.py ROOT CHANGE_DIR SESSION_DIR CHANGE REVIEWER STATUS RISK"
        )

    root = Path(argv[1]).resolve()
    change_dir = Path(argv[2])
    session_dir = Path(argv[3])
    change = argv[4]
    reviewer = argv[5]
    status = argv[6]
    risk = argv[7]

    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "change_dir": str(change_dir),
            "session_dir": str(session_dir),
            "change": change,
            "reviewer": reviewer,
            "status": status,
            "risk": risk,
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "review",
                "start",
                {
                    "root": str(root),
                    "change_dir": str(change_dir),
                    "session_dir": str(session_dir),
                    "change": change,
                    "reviewer": reviewer,
                    "status": status,
                    "risk": risk,
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        data = apply_review(
            change_dir=change_dir,
            session_dir=session_dir,
            change=change,
            reviewer=reviewer,
            status=status,
            risk=risk,
            run_dir=run.run_dir,
        )

        run.logger.info(
            jline(
                "script",
                "review",
                "ok",
                {
                    "change": change,
                    "reviewer": reviewer,
                    "status": data["status"],
                    "risk": risk,
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                **data,
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
        fail(run, "review", error)


if __name__ == "__main__":
    main(sys.argv)
