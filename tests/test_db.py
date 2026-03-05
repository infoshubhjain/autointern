from pathlib import Path

from data.db import JobDB
from data.models import JobListing


def test_db_insert_and_query(tmp_path: Path) -> None:
    db = JobDB(tmp_path / "autointern.db")
    db.init_schema()
    ok = db.insert_job(
        JobListing(
            source="x",
            title="Intern",
            company="A",
            url="https://example.com/job1",
            description="intern role",
        )
    )
    assert ok
    jobs = db.get_jobs_by_status("NEW")
    assert len(jobs) == 1
