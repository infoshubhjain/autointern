from __future__ import annotations

from typing import List, Set, Tuple

from data.models import JobListing
from filtering.keywords import ALLOW_KEYWORDS, BLOCK_KEYWORDS
from filtering.llm_scorer import score_job
from filtering.resume import text_has_resume_overlap


def _is_allowed(job: JobListing, resume_tokens: Set[str] | None = None) -> bool:
    text = f"{job.title} {job.description}".lower()
    if any(block in text for block in BLOCK_KEYWORDS):
        return False
    # User requested: apply to all internships (ignore resume tokens)
    return any(allow in text for allow in ALLOW_KEYWORDS)


def filter_jobs(
    jobs: List[JobListing], min_score: int = 4, resume_tokens: Set[str] | None = None
) -> Tuple[List[JobListing], List[JobListing]]:
    queued: List[JobListing] = []
    skipped: List[JobListing] = []

    for job in jobs:
        if not _is_allowed(job, resume_tokens):
            skipped.append(job)
            continue

        if min_score <= 0:
            queued.append(job)
            continue

        score = score_job(job.description)
        if score >= min_score:
            queued.append(job)
        else:
            skipped.append(job)

    return queued, skipped
