from __future__ import annotations

import json
from typing import Any, Mapping


def jdump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jline(event: str, comp: str, msg: str, extra: dict[str, Any]) -> str:
    if not isinstance(event, str) or not event.strip():
        raise ValueError("event must be non-empty")
    if not isinstance(comp, str) or not comp.strip():
        raise ValueError("comp must be non-empty")
    if not isinstance(msg, str) or not msg.strip():
        raise ValueError("msg must be non-empty")
    data: dict[str, Any] = {"event": event, "comp": comp, "msg": msg}
    data.update(extra)
    return jdump(data)


def is_map(text: str) -> bool:
    data = json.loads(text)
    return isinstance(data, Mapping)
