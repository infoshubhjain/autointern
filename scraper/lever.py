from __future__ import annotations

from typing import Iterable, List

from data.models import JobListing
from scraper.base import BaseScraper
from scraper.utils import get_json, is_intern_title, safe_str, join_text


class LeverScraper(BaseScraper):
    def __init__(self, companies: Iterable[str]) -> None:
        self.companies = [c.strip() for c in companies if c.strip()]

    def fetch(self) -> List[JobListing]:
        jobs: List[JobListing] = []
        for company in self.companies:
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            try:
                payload = get_json(url)
            except Exception:
                continue
            for item in payload:
                title = safe_str(item.get("text"))
                if not is_intern_title(title):
                    continue

                job_url = safe_str(item.get("hostedUrl")) or safe_str(item.get("applyUrl"))
                if not job_url:
                    continue

                description = safe_str(item.get("description"))
                location = safe_str(item.get("categories", {}).get("location"))

                jobs.append(
                    JobListing(
                        source="lever",
                        title=title,
                        company=company,
                        url=job_url,
                        description=join_text([location, description]),
                    )
                )
        return jobs
