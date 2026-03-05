from __future__ import annotations

from typing import Iterable, List

from data.models import JobListing
from scraper.base import BaseScraper
from scraper.utils import get_json, is_intern_title, safe_str, join_text


class SimplifyScraper(BaseScraper):
    def __init__(self, listings_urls: Iterable[str]) -> None:
        self.listings_urls = [u for u in listings_urls if u]

    def fetch(self) -> List[JobListing]:
        payload = None
        last_error = None
        for url in self.listings_urls:
            try:
                payload = get_json(url)
                break
            except Exception as e:
                last_error = e
                continue
        if payload is None:
            raise RuntimeError(f"Failed to fetch listings.json from any URL: {self.listings_urls}") from last_error
        listings = payload.get("listings", payload) if isinstance(payload, dict) else payload
        jobs: List[JobListing] = []

        for item in listings:
            title = safe_str(item.get("title"))
            if not is_intern_title(title):
                continue

            company = safe_str(item.get("company_name")) or safe_str(item.get("company"))
            url = safe_str(item.get("url")) or safe_str(item.get("apply_url"))
            location = safe_str(item.get("location"))
            description = safe_str(item.get("description"))

            if not url:
                continue

            jobs.append(
                JobListing(
                    source="simplify",
                    title=title,
                    company=company or "Unknown",
                    url=url,
                    description=join_text([location, description]),
                )
            )

        return jobs
