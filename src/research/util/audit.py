from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from research.io.json import write_json
from research.io.jsonl import append_jsonl
from research.util.message import Message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_atom(path: str, data: Any) -> str:
    temp = path + ".tmp"
    write_json(temp, data)
    os.replace(temp, path)
    return path


def parse_json(text: str) -> Any:
    if not text:
        raise ValueError("empty text")

    body = text.strip()

    if not body:
        raise ValueError("empty text")

    if body[0] not in "{[":
        raise ValueError("not json")

    return json.loads(body)


@dataclass(slots=True)
class Audit:
    run_dir: str
    meta: dict[str, Any]
    audit_path: str
    log_dir: str
    segment_index: int
    segment_line: int
    segment: list[str]
    status: str
    start_ts: str
    end_ts: str | None
    progress: dict[str, Any] | None
    error: dict[str, Any] | None

    @staticmethod
    def create(run_dir: str, meta: dict[str, Any]) -> Audit:
        os.makedirs(run_dir, exist_ok=True)
        log_dir = os.path.join(run_dir, "_log")
        os.makedirs(log_dir, exist_ok=True)
        audit_path = os.path.join(run_dir, "_audit.json")
        timestamp = utc_now()

        audit = Audit(
            run_dir=run_dir,
            meta=meta,
            audit_path=audit_path,
            log_dir=log_dir,
            segment_index=0,
            segment_line=0,
            segment=["0000.jsonl"],
            status="running",
            start_ts=timestamp,
            end_ts=None,
            progress=None,
            error=None,
        )

        audit.touch()
        audit.flush()
        return audit

    def __call__(self, message: Message) -> None:
        record = self.record(message)
        self.append(record)

        if "payload" in record:
            payload = record["payload"]

            if isinstance(payload, dict) and payload.get("event") == "progress":
                self.set_prog(payload)

    def finish_ok(self) -> None:
        self.status = "success"
        self.end_ts = utc_now()
        self.flush()

    def finish_err(self, error: BaseException) -> None:
        self.status = "error"
        self.end_ts = utc_now()
        self.error = {"type": type(error).__name__, "message": str(error)}
        self.flush()

    def seg_name(self, index: int) -> str:
        return f"{index:04d}.jsonl"

    def seg_path(self) -> str:
        return os.path.join(self.log_dir, self.seg_name(self.segment_index))

    def touch(self) -> None:
        path = self.seg_path()

        if not os.path.isfile(path):
            with open(path, "w", encoding="utf-8"):
                pass

    def rotate(self) -> None:
        if self.segment_line < 16384:
            return

        self.segment_index += 1
        self.segment_line = 0
        name = self.seg_name(self.segment_index)
        self.segment.append(name)
        self.touch()
        self.flush()

    def append(self, record: dict[str, Any]) -> None:
        self.rotate()
        append_jsonl(self.seg_path(), record)
        self.segment_line += 1

        if self.segment_line == 1 or self.segment_line % 256 == 0:
            self.flush()

    def record(self, message: Message) -> dict[str, Any]:
        level = (
            message.level.value
            if hasattr(message.level, "value")
            else str(message.level)
        )
        record: dict[str, Any] = {
            "timestamp": message.timestamp,
            "level": level,
            "text": message.text,
        }

        try:
            payload = parse_json(message.text)
        except ValueError:
            payload = None

        if payload is not None:
            record["payload"] = payload

        return record

    def set_prog(self, payload: dict[str, Any]) -> None:
        self.progress = {
            "name": payload["name"],
            "current": payload["current"],
            "total": payload["total"],
            "elapsed": payload["elapsed"],
            "eta": payload["eta"],
            "rate": payload["rate"],
            "phase": payload["phase"],
        }

        if payload["phase"] == "end" and self.status == "running":
            self.status = "success"
            self.end_ts = utc_now()

        self.flush()

    def flush(self) -> None:
        finger = self.meta["fingerprint"]
        data = {
            "start": self.start_ts,
            "end": self.end_ts,
            "status": self.status,
            "fingerprint": finger,
            "progress": self.progress,
            "log": {
                "dir": "_log",
                "segment": list(self.segment),
                "current": self.seg_name(self.segment_index),
            },
            "error": self.error,
        }
        write_atom(self.audit_path, data)
