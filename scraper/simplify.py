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
            raw_url = safe_str(item.get("url")) or safe_str(item.get("apply_url"))
            company_url = safe_str(item.get("company_url"))
            url = _normalize_url(raw_url, company_url)
            locations = item.get("locations") or []
            if isinstance(locations, list):
                location = ", ".join([safe_str(x) for x in locations if safe_str(x)])
            else:
                location = safe_str(locations)
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


def _normalize_url(url: str, company_url: str) -> str:
    if not url:
        return company_url

    # Greenhouse embed links expire; convert to canonical job board URL when possible.
    if "boards.greenhouse.io/embed/job_app" in url and "token=" in url:
        token = url.split("token=", 1)[1].split("&", 1)[0]
        slug = _extract_greenhouse_slug(company_url)
        if slug:
            return f"https://job-boards.greenhouse.io/{slug}/jobs/{token}"

    # Lever apply URLs can be normalized by removing trailing /apply
    if "jobs.lever.co" in url and url.endswith("/apply"):
        return url[: -len("/apply")]

    return url


def _extract_greenhouse_slug(company_url: str) -> str:
    if not company_url:
        return ""
    for marker in ("job-boards.greenhouse.io/", "boards.greenhouse.io/"):
        if marker in company_url:
            return company_url.split(marker, 1)[1].split("/", 1)[0]
    return ""
