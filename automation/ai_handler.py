from __future__ import annotations

from data.models import JobListing


def build_answer(kind: str, profile: dict, job: JobListing) -> str:
    name = f"{profile.get('first_name', '').strip()} {profile.get('last_name', '').strip()}".strip()
    school = profile.get("school", "")
    degree = profile.get("degree", "")
    grad = profile.get("grad_year", "")
    role = job.title
    company = job.company

    if kind == "motivation":
        return (
            f"I am excited to apply for the {role} role at {company}. "
            f"I'm {name} studying {degree} at {school} (class of {grad}). "
            "I want to contribute to real products while learning from strong engineers."
        )
    if kind == "strength":
        return (
            "My strengths are ownership and fast iteration. I break problems down, "
            "ship small increments, and keep stakeholders updated."
        )
    if kind == "experience":
        return (
            "I have built software projects that involve APIs, data processing, and UI work. "
            "I enjoy collaborating and writing clean, testable code."
        )
    return ""
