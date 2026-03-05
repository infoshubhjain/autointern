from __future__ import annotations

from typing import List

from data.models import JobListing
from scraper.base import BaseScraper


class IndeedScraper(BaseScraper):
    def fetch(self) -> List[JobListing]:
        return [
            JobListing(
                source="indeed",
                title="Software Engineering Co-op",
                company="Riverbyte",
                url="https://www.indeed.com/viewjob?jk=abc123",
                description="Co-op opening for software engineering students.",
            )
        ]
