from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class Req:
    role: str
    text: str
    meta: dict[str, Any]


@dataclass(slots=True)
class Resp:
    provider: str
    model: str
    text: str
    meta: dict[str, Any]


class Provider(Protocol):
    def send(self, req: Req) -> Resp:
        raise NotImplementedError


@dataclass(slots=True)
class Echo:
    model: str

    def send(self, req: Req) -> Resp:
        return Resp(
            provider="echo",
            model=self.model,
            text=req.text,
            meta={
                "role": req.role,
                "size": len(req.text),
                **req.meta,
            },
        )


def read_agent(data: dict[str, Any]) -> dict[str, Any]:
    if "provider" not in data:
        raise KeyError("provider")

    item = data["provider"]

    if not isinstance(item, dict):
        raise TypeError("provider")

    return item


def make_provider(data: dict[str, Any]) -> Provider:
    item = read_agent(data)
    name = item["name"]
    model = item["model"]

    if name == "echo":
        return Echo(model=str(model))

    if name == "gemini":
        from research.agent.gemini import Gemini

        return Gemini(model=str(model))

    raise NotImplementedError(str(name))
