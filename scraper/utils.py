from __future__ import annotations

from typing import Any, Iterable

import requests


def is_intern_title(title: str) -> bool:
    text = title.lower()
    return "intern" in text or "internship" in text or "co-op" in text or "coop" in text


def get_json(url: str, timeout_s: int = 20) -> Any:
    resp = requests.get(url, timeout=timeout_s)
    resp.raise_for_status()
    return resp.json()


def get_optional_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def join_text(parts: Iterable[str], sep: str = " ") -> str:
    return sep.join([p for p in parts if p])
