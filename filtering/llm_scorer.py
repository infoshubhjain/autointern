from __future__ import annotations


def score_job(description: str) -> int:
    """Heuristic relevance score fallback for local/offline use."""
    text = description.lower()
    score = 0
    for token in ("intern", "software", "python", "engineering", "api"):
        if token in text:
            score += 2
    return min(score, 10)
