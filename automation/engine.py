from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

import requests
from playwright.sync_api import sync_playwright

from automation.ai_handler import build_answer
from automation.field_detector import FIELD_MAP
from data.db import JobDB
from data.models import AppResult, JobListing


@dataclass(slots=True)
class ApplicationBot:
    db: JobDB

    def apply(self, job: JobListing) -> AppResult:
        profile = self.db.get_profile()
        if not profile:
            return AppResult(status="FAILED", notes="Missing profile")

        # Preflight the URL; many sources include expired or blocked links.
        try:
            resp = requests.get(job.url, timeout=15, allow_redirects=True)
            if resp.status_code >= 400:
                return AppResult(
                    status="SKIPPED",
                    notes=f"Dead link {resp.status_code}: {resp.url}",
                )
        except Exception as e:
            return AppResult(status="SKIPPED", notes=f"Dead link: {e}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(job.url, wait_until="load", timeout=60000)
                page.wait_for_timeout(2000)

                self._fill_fields(page, profile, job)
                self._submit(page)

                browser.close()
                return AppResult(status="APPLIED", notes="Submitted")
            except Exception as e:
                browser.close()
                return AppResult(status="FAILED", notes=str(e))

    def _submit(self, page) -> None:
        # try common submit selectors
        selectors = [
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "input[type='submit']",
        ]
        for sel in selectors:
            loc = page.locator(sel).first
            if loc.count() > 0:
                loc.click()
                page.wait_for_timeout(3000)
                return

    def _fill_fields(self, page, profile: Dict[str, str], job: JobListing) -> None:
        inputs = page.locator("input, textarea, select")
        count = inputs.count()
        for i in range(count):
            el = inputs.nth(i)
            tag = el.evaluate("el => el.tagName.toLowerCase()")
            input_type = el.get_attribute("type") or ""

            label = self._get_label_text(page, el)
            key = self._map_field(label)

            if input_type == "file":
                resume = profile.get("resume_path")
                if resume:
                    el.set_input_files(resume)
                continue

            if key:
                self._fill_known(el, tag, input_type, key, profile)
                continue

            # unknown field -> attempt auto answer
            question = label or el.get_attribute("name") or el.get_attribute("id") or ""
            question = question.strip()
            if not question:
                continue

            answer = self._auto_answer(question, profile, job)
            if answer is None:
                # queue question for UI
                self.db.create_pending_question(job.id or 0, question)
                raise RuntimeError(f"Pending question: {question}")

            self._fill_value(el, tag, input_type, answer)

    def _fill_known(self, el, tag: str, input_type: str, key: str, profile: Dict[str, str]) -> None:
        value = profile.get(key, "")
        if not value:
            return
        self._fill_value(el, tag, input_type, value)

    def _fill_value(self, el, tag: str, input_type: str, value: str) -> None:
        if tag == "select":
            el.select_option(label=value)
            return
        if input_type in ("checkbox", "radio"):
            if value.lower() in ("yes", "true", "1"):
                el.check()
            return
        el.fill(value)

    def _get_label_text(self, page, el) -> str:
        label = ""
        el_id = el.get_attribute("id")
        if el_id:
            lab = page.locator(f"label[for='{el_id}']").first
            if lab.count() > 0:
                label = lab.inner_text()
        if not label:
            label = el.get_attribute("aria-label") or ""
        if not label:
            label = el.get_attribute("placeholder") or ""
        return label.strip()

    def _map_field(self, label: str) -> str | None:
        normalized = label.lower()
        for key, synonyms in FIELD_MAP.items():
            if any(s in normalized for s in synonyms):
                return key
        return None

    def _auto_answer(self, question: str, profile: Dict[str, str], job: JobListing) -> str | None:
        q = question.lower()

        if "authorized" in q or "work authorization" in q:
            return profile.get("work_authorization")
        if "sponsor" in q or "sponsorship" in q:
            return profile.get("sponsorship")
        if "gpa" in q:
            return profile.get("gpa")
        if "start" in q and "date" in q:
            return profile.get("start_date")
        if "linkedin" in q:
            return profile.get("linkedin")
        if "github" in q:
            return profile.get("github")
        if "portfolio" in q:
            return profile.get("portfolio")

        # open-text questions
        if re.search(r"why|interest|motiv", q):
            return build_answer("motivation", profile, job)
        if re.search(r"strength|weakness|challenge", q):
            return build_answer("strength", profile, job)
        if re.search(r"experience|project", q):
            return build_answer("experience", profile, job)

        # fallback to stored answer if user already provided for similar question
        ans = self.db.find_answer_for_job(job.id or 0, question)
        if ans:
            return ans

        # final fallback to default answer if configured
        default = profile.get("default_answer")
        if default:
            return default

        return None
