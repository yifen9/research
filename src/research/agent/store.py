from __future__ import annotations

from typing import Protocol


class Store(Protocol):
    def add(self, role: str, text: str) -> str: ...

    def find(self, role: str, text: str, limit: int) -> list[str]: ...
