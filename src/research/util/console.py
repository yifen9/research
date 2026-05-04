from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress as RichProgress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from research.util.message import Message


def time_text(timestamp: str) -> str:
    if len(timestamp) < 19:
        raise ValueError("bad timestamp")
    return timestamp[11:19]


def level_style(level: str) -> str:
    if level == "INFO":
        return "green"
    if level == "WARN":
        return "yellow"
    if level == "ERROR":
        return "red"
    raise ValueError(level)


@dataclass(slots=True)
class ConsoleSink:
    console: Console
    transient: bool
    progress: RichProgress | None
    started: bool
    task_id: int | None
    task_name: str | None

    def __call__(self, message: Message) -> None:
        try:
            payload = self.parse(message.text)
        except ValueError:
            payload = message.text

        if isinstance(payload, dict) and payload["event"] == "progress":
            self.handle(message, payload)
            return

        self.print_log(message, payload)

    def parse(self, text: str) -> Any:
        if not text:
            raise ValueError("empty text")
        body = text.strip()
        if not body:
            raise ValueError("empty text")
        if body[0] not in "{[":
            raise ValueError("not json")
        return json.loads(body)

    def ensure(self) -> None:
        if self.progress is not None:
            return

        self.progress = RichProgress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=self.transient,
        )

    def print_line(self, text: str, style: str | None) -> None:
        if self.progress is not None and self.started:
            self.progress.console.print(text, style=style)
            return
        self.console.print(text, style=style)

    def print_log(self, message: Message, payload: Any) -> None:
        timestamp = time_text(message.timestamp)
        level = (
            message.level.value
            if hasattr(message.level, "value")
            else str(message.level)
        )
        style = level_style(level)

        if isinstance(payload, dict):
            event = payload["event"]
            body = payload["msg"]
            extra: list[str] = []

            for key in sorted(payload.keys()):
                if key in {"event", "msg"}:
                    continue
                extra.append(f"{key}={payload[key]}")

            tail = " " + " ".join(extra) if extra else ""
            line = f"[{timestamp}] [{level}] [{event}] {body}{tail}"
        else:
            line = f"[{timestamp}] [{level}] {message.text}"

        self.print_line(line, style)

    def handle(self, message: Message, payload: dict[str, Any]) -> None:
        self.ensure()

        if self.progress is None:
            raise RuntimeError("progress missing")

        phase = payload["phase"]
        name = str(payload["name"])
        total = int(payload["total"])
        current = int(payload["current"])

        if phase == "start":
            self.task_name = name
            self.print_start(message, payload)
            if not self.started:
                self.progress.start()
                self.started = True
            self.task_id = self.progress.add_task(name, total=total, completed=0)
            return

        if phase == "step":
            if self.task_id is None:
                raise RuntimeError("progress step before start")
            self.progress.update(
                self.task_id, total=total, completed=current, description=name
            )
            return

        if phase == "end":
            if self.task_id is None:
                raise RuntimeError("progress end before start")
            self.progress.update(
                self.task_id, total=total, completed=total, description=name
            )
            self.print_end(message, payload)
            if self.started:
                self.progress.stop()
                self.started = False
            self.task_id = None
            self.task_name = None
            return

        raise ValueError(phase)

    def print_start(self, message: Message, payload: dict[str, Any]) -> None:
        timestamp = time_text(message.timestamp)
        style = level_style("INFO")
        self.print_line(f"[{timestamp}] [INFO] [progress] start", style)
        self.print_line(f"  name: {payload['name']}", None)
        self.print_line(f"  total: {payload['total']}", None)

    def print_end(self, message: Message, payload: dict[str, Any]) -> None:
        timestamp = time_text(message.timestamp)
        style = level_style("INFO")
        self.print_line(f"[{timestamp}] [INFO] [progress] end", style)
        self.print_line(f"  name: {payload['name']}", None)
        self.print_line(f"  total: {payload['total']}", None)
        self.print_line(f"  elapsed: {payload['elapsed']}", None)
        self.print_line(f"  rate: {payload['rate']}", None)


def make_console(transient: bool) -> ConsoleSink:
    return ConsoleSink(
        console=Console(markup=False),
        transient=transient,
        progress=None,
        started=False,
        task_id=None,
        task_name=None,
    )
