from __future__ import annotations

from typing import List

from data.models import JobListing
from scraper.base import BaseScraper


class LinkedInScraper(BaseScraper):
    def fetch(self) -> List[JobListing]:
        return [
            JobListing(
                source="linkedin",
                title="Software Engineering Intern",
                company="Acme Robotics",
                url="https://www.linkedin.com/jobs/view/12345",
                description="Looking for SWE intern with Python and APIs.",
            ),
            JobListing(
                source="linkedin",
                title="Backend Intern",
                company="Nimbus Labs",
                url="https://www.linkedin.com/jobs/view/12346",
                description="Internship role focused on backend services.",
            ),
        ]
