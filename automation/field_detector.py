from __future__ import annotations

from typing import Dict, Iterable

FIELD_MAP = {
    "first_name": ["first name", "first", "fname", "given name"],
    "last_name": ["last name", "last", "lname", "surname"],
    "email": ["email", "e-mail", "email address"],
    "phone": ["phone", "mobile", "telephone"],
    "university": ["school", "university", "college"],
    "linkedin": ["linkedin", "linkedin url"],
    "github": ["github", "portfolio"],
    "resume": ["resume", "cv", "upload resume"],
}


def match_field(label: str) -> str | None:
    normalized = label.strip().lower()
    for key, synonyms in FIELD_MAP.items():
        if any(syn in normalized for syn in synonyms):
            return key
    return None


def detect_fields(labels: Iterable[str]) -> Dict[str, str]:
    matches: Dict[str, str] = {}
    for label in labels:
        key = match_field(label)
        if key and key not in matches:
            matches[key] = label
    return matches
