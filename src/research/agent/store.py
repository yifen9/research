from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Protocol
from uuid import NAMESPACE_URL, uuid5

from research.io.jsonl import append_jsonl, read_jsonl, write_jsonl


class Store(Protocol):
    def connect(self) -> None: ...

    def add(self, role: str, text: str, meta: dict[str, Any] | None) -> str: ...

    def find(self, role: str, text: str, limit: int) -> list[str]: ...

    def has(self, key: str) -> bool: ...


def part_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@dataclass(slots=True)
class LocalJsonlStore:
    path: Path

    def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, role: str, text: str, meta: dict[str, Any] | None) -> str:
        key = store_key(role, text, meta)
        if self.has(key):
            return key
        self.connect()
        append_jsonl(
            str(self.path),
            {
                "id": key,
                "role": role,
                "text": text,
                "meta": meta or {},
            },
        )
        return key

    def find(self, role: str, text: str, limit: int) -> list[str]:
        if not self.path.is_file():
            return []

        part = part_set(text)
        data: list[tuple[int, str]] = []

        for item in read_jsonl(str(self.path)):
            if not isinstance(item, dict):
                continue
            if item.get("role") != role:
                continue
            item_text = item.get("text")
            if not isinstance(item_text, str):
                continue
            count = len(part & part_set(item_text))
            if count > 0:
                data.append((count, item_text))

        data.sort(key=lambda item: item[0], reverse=True)
        return [text for _, text in data[:limit]]

    def has(self, key: str) -> bool:
        if not self.path.is_file():
            return False

        for item in read_jsonl(str(self.path)):
            if isinstance(item, dict) and item.get("id") == key:
                return True

        return False


@dataclass(slots=True)
class QdrantStore:
    path: Path
    collection: str
    model: str

    def connect(self) -> None:
        from qdrant_client import QdrantClient

        self.path.mkdir(parents=True, exist_ok=True)
        store = QdrantClient(path=str(self.path / "data"))
        store.set_model(self.model, cache_dir=str(self.path / "model"), lazy_load=True)

    def add(self, role: str, text: str, meta: dict[str, Any] | None) -> str:
        key = store_key(role, text, meta)
        if self.has(key):
            return key
        data = meta or {}
        data["role"] = role
        store = self.make()
        store.add(
            collection_name=self.collection,
            documents=[text],
            metadata=[data],
            ids=[str(uuid5(NAMESPACE_URL, key))],
        )
        self.write_index(key, role, text, data)
        return key

    def find(self, role: str, text: str, limit: int) -> list[str]:
        store = self.make()
        data = store.query(
            collection_name=self.collection, query_text=text, limit=limit
        )
        output: list[str] = []

        for item in data:
            meta = item.metadata or {}
            if meta.get("role") == role and isinstance(item.document, str):
                output.append(item.document)

        return output

    def has(self, key: str) -> bool:
        path = self.index_file()
        if not path.is_file():
            return False

        for item in read_jsonl(str(path)):
            if isinstance(item, dict) and item.get("id") == key:
                return True

        return False

    def make(self) -> Any:
        from qdrant_client import QdrantClient

        self.connect()
        store = QdrantClient(path=str(self.path / "data"))
        store.set_model(self.model, cache_dir=str(self.path / "model"), lazy_load=True)
        return store

    def index_file(self) -> Path:
        return self.path / "index.jsonl"

    def write_index(self, key: str, role: str, text: str, meta: dict[str, Any]) -> Path:
        path = self.index_file()
        append_jsonl(str(path), {"id": key, "role": role, "text": text, "meta": meta})
        return path


def store_key(role: str, text: str, meta: dict[str, Any] | None) -> str:
    data = meta or {}
    if "message_id" in data:
        return str(data["message_id"])
    if "id" in data:
        return str(data["id"])
    return sha256(f"{role}\n{text}".encode("utf-8")).hexdigest()


def ensure_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        write_jsonl(str(path), [])
    return path


def default_store(path: Path) -> Store:
    return LocalJsonlStore(path)


def qdrant_store(path: Path, collection: str, model: str) -> Store:
    ensure_file(path / "index.jsonl")
    return QdrantStore(path, collection, model)
