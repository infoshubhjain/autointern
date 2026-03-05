from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from data.models import JobListing
from scraper.ashby import AshbyScraper
from scraper.greenhouse import GreenhouseScraper
from scraper.lever import LeverScraper
from scraper.simplify import SimplifyScraper
from scraper.workable import WorkableScraper


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "ats_companies.yaml"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def scrape_all_sources() -> List[JobListing]:
    cfg = _load_config()
    jobs: List[JobListing] = []

    simplify_cfg = cfg.get("simplify", {})
    listings_urls = simplify_cfg.get("listings_urls") or [
        "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/listings.json",
        "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/main/listings.json",
    ]
    if isinstance(listings_urls, str):
        listings_urls = [listings_urls]
    jobs.extend(SimplifyScraper(listings_urls).fetch())

    greenhouse = cfg.get("greenhouse", [])
    jobs.extend(GreenhouseScraper(greenhouse).fetch())

    lever = cfg.get("lever", [])
    jobs.extend(LeverScraper(lever).fetch())

    ashby = cfg.get("ashby", [])
    jobs.extend(AshbyScraper(ashby).fetch())

    workable = cfg.get("workable", [])
    jobs.extend(WorkableScraper(workable).fetch())

    return jobs
