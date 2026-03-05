from __future__ import annotations

from typing import Iterable, List

from data.models import JobListing
from scraper.base import BaseScraper
from scraper.utils import get_json, is_intern_title, safe_str


class GreenhouseScraper(BaseScraper):
    def __init__(self, companies: Iterable[str]) -> None:
        self.companies = [c.strip() for c in companies if c.strip()]

    def fetch(self) -> List[JobListing]:
        jobs: List[JobListing] = []
        for company in self.companies:
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
            try:
                payload = get_json(url)
            except Exception:
                continue
            for item in payload.get("jobs", []):
                title = safe_str(item.get("title"))
                if not is_intern_title(title):
                    continue

                job_url = safe_str(item.get("absolute_url"))
                if not job_url:
                    continue

                description = safe_str(item.get("content"))
                jobs.append(
                    JobListing(
                        source="greenhouse",
                        title=title,
                        company=safe_str(item.get("company_name")) or company,
                        url=job_url,
                        description=description,
                    )
                )
        return jobs
