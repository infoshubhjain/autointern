from __future__ import annotations

from pathlib import Path

from automation.engine import ApplicationBot
from automation.tracker import Tracker
from data.db import JobDB
from filtering.filter import filter_jobs
from filtering.resume import extract_resume_tokens
from scraper.scraper import scrape_all_sources


def run_pipeline(db_path: Path) -> None:
    db = JobDB(db_path)
    db.init_schema()

    jobs = scrape_all_sources()
    for job in jobs:
        db.insert_job(job)

    profile = db.get_profile()
    resume_tokens = extract_resume_tokens(profile.get("resume_path")) if profile else set()

    new_jobs = db.get_jobs_by_status("NEW")
    queued, skipped = filter_jobs(new_jobs, min_score=0, resume_tokens=resume_tokens)
    for job in queued:
        db.update_status(job.id, "QUEUED", "Passed keyword filter")
    for job in skipped:
        db.update_status(job.id, "SKIPPED", "Failed keyword filter")

    tracker = Tracker(db)
    bot = ApplicationBot(db)
    queued_jobs = db.get_jobs_by_status("QUEUED")
    for job in queued_jobs:
        db.update_status(job.id, "IN_PROGRESS")
        result = bot.apply(job)
        tracker.track_result(job.id, result.status, result.notes)
