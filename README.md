# AutoIntern

API-first internship collector + direct auto-apply.

## What works now
- API-based scrapers: Simplify, Greenhouse, Lever, Ashby, Workable.
- SQLite storage with dedup + status tracking.
- Direct auto-apply via Playwright (headless).
- Web UI for profile, resume upload, and pending question answers.
- Filter can match jobs by words found in your resume PDF.

## Quick start
```bash
cd /Users/shubh/Desktop/gh/autointern
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py init-db
python web/app.py
```

Open `http://127.0.0.1:5179` and fill your profile, upload resume, then click Run AutoApply.

## Notes
- Unknown questions pause that job and appear in the UI under Pending Questions.
- Answer them in the UI and rerun AutoApply to continue those jobs.
- If you want to re-run filtering on previously skipped jobs: `python main.py reset-skipped`
