"""Persistent question indexes; candidate answers remain in the browser only."""
import json
import os
import sqlite3
import threading
from pathlib import Path

DATA_DIR = Path(
    os.environ.get("FUTURESKILL_DATA_DIR", Path(__file__).resolve().parents[1] / "instance")
)
DB_PATH = Path(os.environ.get("HISTORY_DB", DATA_DIR / "interview_history.sqlite3"))
lock = threading.RLock()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.execute("PRAGMA busy_timeout=15000")
    return connection


def init():
    with connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS questions
            (id INTEGER PRIMARY KEY AUTOINCREMENT, guest_id TEXT NOT NULL,
            session_id TEXT NOT NULL, question TEXT NOT NULL, career TEXT NOT NULL,
            embedding TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_guest_id ON questions (guest_id,id)")


def personal(guest_id):
    if not guest_id:
        return []
    with lock, connect() as connection:
        return connection.execute(
            "SELECT question FROM questions WHERE guest_id=? ORDER BY id", (guest_id,)
        ).fetchall()


def all_text(guest_id):
    return [row[0] for row in personal(guest_id)]


def global_count():
    with lock, connect() as connection:
        return connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]


def insert(guest_id, session_id, question, career, embedding=None):
    with lock, connect() as connection:
        connection.execute(
            "INSERT INTO questions(guest_id,session_id,question,career,embedding) VALUES(?,?,?,?,?)",
            (guest_id, session_id, question, career, json.dumps(embedding) if embedding else None),
        )
