from __future__ import annotations

import hashlib
import json
import sqlite3
import re
import difflib
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from data.models import JobListing


class JobDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    url_hash TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pending_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    norm_question TEXT NOT NULL,
                    answer TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    answered_at TIMESTAMP DEFAULT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                );

                CREATE TABLE IF NOT EXISTS question_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    norm_question TEXT NOT NULL UNIQUE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
                CREATE INDEX IF NOT EXISTS idx_apps_job_id ON applications(job_id);
                CREATE INDEX IF NOT EXISTS idx_pending_job_id ON pending_questions(job_id);
                CREATE INDEX IF NOT EXISTS idx_question_norm ON question_answers(norm_question);
                """
            )
            # Lightweight migration for older DBs
            cols = [r[1] for r in conn.execute("PRAGMA table_info(pending_questions)").fetchall()]
            if "norm_question" not in cols:
                conn.execute("ALTER TABLE pending_questions ADD COLUMN norm_question TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def normalize_question(question: str) -> str:
        text = question.lower()
        text = re.sub(r"[^a-z0-9\\s]", " ", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return text

    @staticmethod
    def dedup_hash(url: str) -> str:
        return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:16]

    def insert_job(self, job: JobListing) -> bool:
        self.init_schema()
        url_hash = self.dedup_hash(job.url)
        with self._conn() as conn:
            existing = conn.execute("SELECT id FROM jobs WHERE url_hash = ?", (url_hash,)).fetchone()
            if existing:
                return False
            conn.execute(
                """
                INSERT INTO jobs(source, title, company, url, url_hash, description, status)
                VALUES (?, ?, ?, ?, ?, ?, 'NEW')
                """,
                (job.source, job.title, job.company, job.url, url_hash, job.description),
            )
            return True

    def get_jobs_by_status(self, status: str, limit: Optional[int] = None) -> List[JobListing]:
        sql = (
            "SELECT id, source, title, company, url, description, url_hash "
            "FROM jobs WHERE status = ? ORDER BY id ASC"
        )
        params: Iterable[object]
        if limit is not None:
            sql += " LIMIT ?"
            params = (status, limit)
        else:
            params = (status,)

        with self._conn() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [
                JobListing(
                    id=row["id"],
                    source=row["source"],
                    title=row["title"],
                    company=row["company"],
                    url=row["url"],
                    description=row["description"],
                    url_hash=row["url_hash"],
                )
                for row in rows
            ]

    def update_status(self, job_id: int | None, status: str, notes: str = "") -> None:
        if job_id is None:
            return
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, job_id),
            )
            if notes:
                conn.execute(
                    "INSERT INTO applications(job_id, status, notes) VALUES (?, ?, ?)",
                    (job_id, status, notes),
                )

    def count_by_status(self) -> List[Tuple[str, int]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS c FROM jobs GROUP BY status ORDER BY status"
            ).fetchall()
            return [(row["status"], int(row["c"])) for row in rows]

    def upsert_profile(self, data: dict) -> None:
        payload = json.dumps(data)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO user_profile(id, data) VALUES (1, ?) "
                "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                (payload,),
            )

    def get_profile(self) -> dict:
        with self._conn() as conn:
            row = conn.execute("SELECT data FROM user_profile WHERE id = 1").fetchone()
            if not row:
                return {}
            return json.loads(row["data"])

    def create_pending_question(self, job_id: int, question: str) -> int:
        norm = self.normalize_question(question)
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO pending_questions(job_id, question, norm_question) VALUES (?, ?, ?)",
                (job_id, question, norm),
            )
            return int(cur.lastrowid)

    def get_pending_questions(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, job_id, question FROM pending_questions WHERE answer IS NULL ORDER BY id ASC"
            ).fetchall()
            return [dict(row) for row in rows]

    def set_question_answer(self, qid: int, answer: str) -> None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT question, norm_question FROM pending_questions WHERE id = ?",
                (qid,),
            ).fetchone()
            if not row:
                return
            question = row["question"]
            norm = row["norm_question"]
            conn.execute(
                "UPDATE pending_questions SET answer = ?, answered_at = CURRENT_TIMESTAMP WHERE id = ?",
                (answer, qid),
            )
            conn.execute(
                "INSERT INTO question_answers(norm_question, question, answer) VALUES (?, ?, ?) "
                "ON CONFLICT(norm_question) DO UPDATE SET answer=excluded.answer",
                (norm, question, answer),
            )

    def find_answer_for_job(self, job_id: int, question: str) -> str | None:
        norm = self.normalize_question(question)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT answer FROM question_answers WHERE norm_question = ?",
                (norm,),
            ).fetchone()
            if row:
                return row["answer"]
        # Fuzzy fallback against known questions
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT norm_question, answer FROM question_answers"
            ).fetchall()
            if not rows:
                return None
            best_score = 0.0
            best_answer = None
            for r in rows:
                score = difflib.SequenceMatcher(None, norm, r["norm_question"]).ratio()
                if score > best_score:
                    best_score = score
                    best_answer = r["answer"]
            if best_score >= 0.86:
                return best_answer
        return None

    def list_applied_jobs(self, limit: int = 200) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, title, company, url, updated_at FROM jobs "
                "WHERE status = 'APPLIED' ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_unsuccessful_jobs(self, limit: int = 200) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, title, company, url, status, updated_at FROM jobs "
                "WHERE status IN ('FAILED', 'SKIPPED') ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_jobs(self, limit: int = 500, status: str | None = None, search: str | None = None) -> List[dict]:
        params: list = []
        sql = "SELECT id, title, company, url, status, updated_at FROM jobs"
        clauses = []
        if status and status != "ALL":
            clauses.append("status = ?")
            params.append(status)
        if search:
            clauses.append("(title LIKE ? OR company LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def reset_status(self, from_status: str, to_status: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE status = ?",
                (to_status, from_status),
            )
            return int(cur.rowcount)
