from __future__ import annotations

from typing import Iterable, List

from data.models import JobListing
from scraper.base import BaseScraper
from scraper.utils import get_json, is_intern_title, safe_str, join_text


class AshbyScraper(BaseScraper):
    def __init__(self, companies: Iterable[str]) -> None:
        self.companies = [c.strip() for c in companies if c.strip()]

    def fetch(self) -> List[JobListing]:
        jobs: List[JobListing] = []
        for company in self.companies:
            url = (
                "https://api.ashbyhq.com/posting-api/job-board/"
                f"{company}?includeCompensation=true"
            )
            try:
                payload = get_json(url)
            except Exception:
                continue
            postings = payload.get("jobs", [])
            for item in postings:
                title = safe_str(item.get("title"))
                if not is_intern_title(title):
                    continue

                job_url = safe_str(item.get("jobUrl"))
                if not job_url:
                    continue

                description = safe_str(item.get("descriptionHtml"))
                location = safe_str(item.get("location"))

                jobs.append(
                    JobListing(
                        source="ashby",
                        title=title,
                        company=company,
                        url=job_url,
                        description=join_text([location, description]),
                    )
                )
        return jobs
