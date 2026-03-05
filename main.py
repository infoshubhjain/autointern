from __future__ import annotations

from pathlib import Path
from typing import List

import click

from automation.engine import ApplicationBot
from automation.runner import run_pipeline
from automation.tracker import Tracker
from data.db import JobDB
from data.models import JobListing
from filtering.filter import filter_jobs
from filtering.resume import extract_resume_tokens
from scraper.scraper import scrape_all_sources

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "autointern.db"


def _db() -> JobDB:
    return JobDB(DEFAULT_DB)


@click.group()
def cli() -> None:
    """AutoIntern CLI."""


@cli.command()
def init_db() -> None:
    db = _db()
    db.init_schema()
    click.echo(f"Initialized DB at {db.db_path}")


@cli.command()
def scrape() -> None:
    db = _db()
    db.init_schema()
    jobs = scrape_all_sources()
    inserted = 0
    for job in jobs:
        if db.insert_job(job):
            inserted += 1
    click.echo(f"Scraped {len(jobs)} jobs. Inserted {inserted} new records.")


@cli.command()
def filter() -> None:
    db = _db()
    new_jobs = db.get_jobs_by_status("NEW")
    profile = db.get_profile()
    resume_tokens = extract_resume_tokens(profile.get("resume_path")) if profile else set()
    queued, skipped = filter_jobs(new_jobs, min_score=0, resume_tokens=resume_tokens)
    for job in queued:
        db.update_status(job.id, "QUEUED", "Passed keyword filter")
    for job in skipped:
        db.update_status(job.id, "SKIPPED", "Failed keyword filter")
    click.echo(f"Queued {len(queued)} jobs, skipped {len(skipped)} jobs.")


@cli.command()
def apply() -> None:
    db = _db()
    tracker = Tracker(db)
    bot = ApplicationBot(db)
    queued_jobs: List[JobListing] = db.get_jobs_by_status("QUEUED")

    if not queued_jobs:
        click.echo("No QUEUED jobs found.")
        return

    applied = 0
    failed = 0

    for job in queued_jobs:
        db.update_status(job.id, "IN_PROGRESS")
        result = bot.apply(job)
        tracker.track_result(job.id, result.status, result.notes)
        if result.status == "APPLIED":
            applied += 1
        else:
            failed += 1

    click.echo(f"Processed {len(queued_jobs)} jobs. APPLIED={applied}, non-applied={failed}")


@cli.command()
def run() -> None:
    run_pipeline(DEFAULT_DB)


@cli.command()
def report() -> None:
    db = _db()
    stats = db.count_by_status()
    if not stats:
        click.echo("No jobs in database.")
        return

    click.echo("Status report:")
    for status, count in stats:
        click.echo(f"  {status:<14} {count}")


@cli.command("reset-skipped")
def reset_skipped() -> None:
    db = _db()
    count = db.reset_status("SKIPPED", "NEW")
    click.echo(f"Reset {count} SKIPPED jobs to NEW.")


if __name__ == "__main__":
    cli()
