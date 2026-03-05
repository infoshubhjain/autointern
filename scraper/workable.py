from __future__ import annotations

from typing import Iterable, List

from data.models import JobListing
from scraper.base import BaseScraper
from scraper.utils import get_json, is_intern_title, safe_str, join_text


class WorkableScraper(BaseScraper):
    def __init__(self, companies: Iterable[str]) -> None:
        self.companies = [c.strip() for c in companies if c.strip()]

    def fetch(self) -> List[JobListing]:
        jobs: List[JobListing] = []
        for company in self.companies:
            url = f"https://apply.workable.com/api/v1/widget/accounts/{company}"
            try:
                payload = get_json(url)
            except Exception:
                continue
            for item in payload.get("jobs", []):
                title = safe_str(item.get("title"))
                if not is_intern_title(title):
                    continue

                job_url = safe_str(item.get("url"))
                if not job_url:
                    continue

                description = safe_str(item.get("description"))
                location = safe_str(item.get("location"))

                jobs.append(
                    JobListing(
                        source="workable",
                        title=title,
                        company=safe_str(item.get("company")) or company,
                        url=job_url,
                        description=join_text([location, description]),
                    )
                )
        return jobs
