from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Set

from PyPDF2 import PdfReader


_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "are",
    "was",
    "were",
    "you",
    "your",
    "our",
    "their",
    "will",
    "have",
    "has",
    "had",
    "not",
    "but",
    "all",
    "any",
    "can",
    "able",
    "use",
    "using",
    "used",
    "work",
    "works",
    "working",
    "team",
    "teams",
    "project",
    "projects",
    "experience",
    "skills",
    "skill",
    "year",
    "years",
}


def _tokenize(text: str) -> Set[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def extract_resume_tokens(resume_path: str | None) -> Set[str]:
    if not resume_path:
        return set()
    path = Path(resume_path)
    if not path.exists():
        return set()
    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return _tokenize(" ".join(pages))
    except Exception:
        return set()


def text_has_resume_overlap(text: str, resume_tokens: Iterable[str]) -> bool:
    tokens = _tokenize(text)
    resume_set = set(resume_tokens)
    if not resume_set:
        return False
    return len(tokens.intersection(resume_set)) > 0
