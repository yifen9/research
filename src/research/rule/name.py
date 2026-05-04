from __future__ import annotations

import re


def split_name(name: str) -> list[str]:
    text = name.replace("-", "_")
    return [item for item in text.split("_") if item]


def good_word(name: str, pool: set[str]) -> bool:
    part = split_name(name)

    if len(part) > 2:
        return False

    for item in part:
        if item not in pool:
            return False

    return True


def good_kebab(name: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) is not None


def good_snake(name: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", name) is not None