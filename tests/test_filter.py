from data.models import JobListing
from filtering.filter import filter_jobs


def test_filter_jobs_keeps_intern_roles() -> None:
    jobs = [
        JobListing(
            source="x",
            title="Software Engineering Intern",
            company="A",
            url="https://example.com/1",
            description="Python software engineering intern role",
        ),
        JobListing(
            source="x",
            title="Senior Engineer",
            company="B",
            url="https://example.com/2",
            description="Full-time senior role",
        ),
    ]

    queued, skipped = filter_jobs(jobs)
    assert len(queued) == 1
    assert len(skipped) == 1
