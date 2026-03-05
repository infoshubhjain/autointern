from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from automation.runner import run_pipeline
from data.db import JobDB

DB_PATH = APP_ROOT / "data" / "autointern.db"
ASSETS_DIR = APP_ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

_db = JobDB(DB_PATH)
_db.init_schema()


@app.get("/")
def index() -> Any:
    return send_from_directory(APP_ROOT / "web", "index.html")


@app.get("/api/profile")
def get_profile() -> Any:
    profile = _db.get_profile()
    return jsonify(profile)


@app.post("/api/profile")
def set_profile() -> Any:
    data = request.get_json(force=True)
    _db.upsert_profile(data)
    return jsonify({"ok": True})


@app.post("/api/upload/resume")
def upload_resume() -> Any:
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "missing file"}), 400
    f = request.files["file"]
    dest = ASSETS_DIR / "resume.pdf"
    f.save(dest)
    _db.upsert_profile({"resume_path": str(dest)})
    return jsonify({"ok": True, "path": str(dest)})


@app.post("/api/upload/cover")
def upload_cover() -> Any:
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "missing file"}), 400
    f = request.files["file"]
    dest = ASSETS_DIR / "cover_letter.pdf"
    f.save(dest)
    _db.upsert_profile({"cover_letter_path": str(dest)})
    return jsonify({"ok": True, "path": str(dest)})


@app.get("/api/pending")
def pending_questions() -> Any:
    pending = _db.get_pending_questions()
    return jsonify(pending)


@app.post("/api/answer")
def answer_question() -> Any:
    data = request.get_json(force=True)
    question_id = int(data.get("id"))
    answer = str(data.get("answer", "")).strip()
    if not answer:
        return jsonify({"ok": False, "error": "empty answer"}), 400
    _db.set_question_answer(question_id, answer)
    return jsonify({"ok": True})

@app.get("/api/applied")
def applied_list() -> Any:
    return jsonify(_db.list_applied_jobs())

@app.get("/api/unsuccessful")
def unsuccessful_list() -> Any:
    return jsonify(_db.list_unsuccessful_jobs())


@app.post("/api/run")
def run_now() -> Any:
    def _run() -> None:
        run_pipeline(DB_PATH)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5179, debug=False)
