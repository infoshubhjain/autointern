from __future__ import annotations

from data.db import JobDB


class Tracker:
    def __init__(self, db: JobDB) -> None:
        self.db = db

    def track_result(self, job_id: int, status: str, notes: str = "") -> None:
        self.db.update_status(job_id, status, notes)
