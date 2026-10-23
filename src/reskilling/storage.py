"""Persistent SQLite store. Each anonymous browser session sees only its own data."""

import json
from contextlib import contextmanager
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @contextmanager
    def db(self):
        connection = self.connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    career TEXT NOT NULL,
                    week_index INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    skill TEXT NOT NULL,
                    hours REAL NOT NULL,
                    objective TEXT NOT NULL,
                    activity TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT,
                    proof_path TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS tasks_user ON tasks(user_id, career, completed);
            """)

    def get_profile(self, user_id):
        with self.db() as db:
            row = db.execute("SELECT profile_json FROM profiles WHERE user_id=?", (user_id,)).fetchone()
            return json.loads(row["profile_json"]) if row else None

    def save_profile(self, user_id, profile):
        with self.db() as db:
            db.execute("""INSERT INTO profiles(user_id,profile_json,created_at,updated_at)
                VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE
                SET profile_json=excluded.profile_json, updated_at=excluded.updated_at""",
                (user_id, json.dumps(profile), now(), now()))

    def list_tasks(self, user_id, career=None):
        with self.db() as db:
            if career:
                rows = db.execute("""SELECT * FROM tasks WHERE user_id=? AND career=?
                    ORDER BY due_date, week_index, CASE kind WHEN 'learning' THEN 0 ELSE 1 END, id""",
                    (user_id, career)).fetchall()
            else:
                rows = db.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,)).fetchall()
            return [dict(row) for row in rows]

    def get_task(self, user_id, task_id):
        with self.db() as db:
            row = db.execute("SELECT * FROM tasks WHERE user_id=? AND id=?", (user_id, task_id)).fetchone()
            return dict(row) if row else None

    def insert_plan(self, user_id, career, tasks):
        """Replace unfinished tasks; preserve all completed task records and uploads."""
        with self.db() as db:
            # Remove old uploaded proof files on unfinished tasks, if any.
            obsolete = [r[0] for r in db.execute(
                "SELECT proof_path FROM tasks WHERE user_id=? AND completed=0 AND proof_path IS NOT NULL",
                (user_id,)).fetchall()]
            db.execute("DELETE FROM tasks WHERE user_id=? AND completed=0", (user_id,))
            created = now()
            for item in tasks:
                db.execute("""INSERT INTO tasks
                    (id,user_id,career,week_index,day,due_date,skill,hours,objective,activity,kind,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(uuid.uuid4()), user_id, career, item["week_index"], item["day"], item["due_date"],
                     item["skill"], item["hours"], item["objective"], item["activity"], item["kind"], created))
        return obsolete

    def set_status(self, user_id, task_id, completed):
        with self.db() as db:
            row = db.execute("SELECT * FROM tasks WHERE user_id=? AND id=?", (user_id, task_id)).fetchone()
            if not row:
                return None
            if bool(row["completed"]) != bool(completed):
                db.execute("UPDATE tasks SET completed=?, completed_at=? WHERE id=? AND user_id=?",
                           (int(bool(completed)), now() if completed else None, task_id, user_id))
            return dict(db.execute("SELECT * FROM tasks WHERE user_id=? AND id=?", (user_id, task_id)).fetchone())

    def set_proof(self, user_id, task_id, filename):
        with self.db() as db:
            row = db.execute("SELECT proof_path FROM tasks WHERE user_id=? AND id=?", (user_id, task_id)).fetchone()
            if not row:
                return None, False
            old = row["proof_path"]
            db.execute("UPDATE tasks SET proof_path=? WHERE user_id=? AND id=?", (filename, user_id, task_id))
            return old, True
