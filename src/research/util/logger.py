from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from research.util.message import Level, Message, make_message


Sink = Callable[[Message], None]


@dataclass(slots=True)
class Logger:
    sink: list[Sink]

    def emit(self, level: Level, text: str) -> Message:
        message = make_message(level, text)
        for item in self.sink:
            item(message)
        return message

    def info(self, text: str) -> Message:
        return self.emit(Level.INFO, text)

    def warn(self, text: str) -> Message:
        return self.emit(Level.WARN, text)

    def error(self, text: str) -> Message:
        return self.emit(Level.ERROR, text)


def make_logger(sink: list[Sink]) -> Logger:
    return Logger(sink=sink)
