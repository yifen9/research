from __future__ import annotations

import csv
import io
from typing import Iterable


def format_csv(rows: Iterable[Iterable[str]], header: Iterable[str] | None) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    if header is not None:
        writer.writerow(list(header))
    for row in rows:
        writer.writerow(list(row))
    return buffer.getvalue()


def write_csv(
    path: str, rows: Iterable[Iterable[str]], header: Iterable[str] | None
) -> str:
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        if header is not None:
            writer.writerow(list(header))
        for row in rows:
            writer.writerow(list(row))
    return path


def read_csv(path: str, has_header: bool) -> tuple[list[str] | None, list[list[str]]]:
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        header: list[str] | None = None
        rows: list[list[str]] = []
        if has_header:
            header = next(reader)
        for row in reader:
            rows.append(list(row))
        return header, rows
