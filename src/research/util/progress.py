from __future__ import annotations

import time
from dataclasses import dataclass

from research.util.jlog import jdump
from research.util.logger import Logger


@dataclass(slots=True)
class Progress:
    logger: Logger
    name: str
    total: int
    current: int
    started: bool
    start_time: float

    def start(self) -> None:
        self.start_time = time.perf_counter()
        self.current = 0
        self.started = True
        self.emit("start")

    def step(self, count: int) -> None:
        if not self.started:
            raise RuntimeError("progress not started")
        self.current += count
        if self.current > self.total:
            raise ValueError("progress over total")
        self.emit("step")

    def finish(self) -> None:
        if not self.started:
            raise RuntimeError("progress not started")
        self.current = self.total
        self.emit("end")
        self.started = False

    def emit(self, phase: str) -> None:
        elapsed = time.perf_counter() - self.start_time
        rate = self.current / elapsed if elapsed > 0.0 else 0.0
        remain = self.total - self.current
        eta = remain / rate if rate > 0.0 else None
        pct = self.current / self.total if self.total > 0 else 1.0

        data = {
            "event": "progress",
            "phase": phase,
            "name": self.name,
            "current": self.current,
            "total": self.total,
            "pct": pct,
            "elapsed": elapsed,
            "rate": rate,
            "eta": eta,
        }

        self.logger.info(jdump(data))


def make_progress(logger: Logger, name: str, total: int) -> Progress:
    return Progress(
        logger=logger,
        name=name,
        total=total,
        current=0,
        started=False,
        start_time=0.0,
    )
