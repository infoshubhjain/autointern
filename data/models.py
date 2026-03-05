from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class JobListing:
    source: str
    title: str
    company: str
    url: str
    description: str
    id: Optional[int] = None
    url_hash: Optional[str] = None


@dataclass(slots=True)
class AppResult:
    status: str
    notes: str = ""
