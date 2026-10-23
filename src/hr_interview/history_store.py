"""Persistent question indexes. SQLite MVP; use managed Postgres for Render production.
No user transcripts or recordings stored server-side. Cookie carries opaque guest ID.
"""
import sqlite3, os, json, threading
from pathlib import Path
DB_PATH = os.getenv('HISTORY_DB',str(Path(__file__).parent/'interview_history.sqlite3'))
lock = threading.RLock()

def connect():
    conn=sqlite3.connect(DB_PATH,timeout=15)
    conn.execute('PRAGMA busy_timeout=15000')
    return conn

def init():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS questions
        (id INTEGER PRIMARY KEY AUTOINCREMENT, guest_id TEXT NOT NULL,
        session_id TEXT NOT NULL, question TEXT NOT NULL, career TEXT NOT NULL,
        embedding TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute('CREATE INDEX IF NOT EXISTS idx_guest_id ON questions (guest_id,id)')

def personal(guest_id):
    with lock, connect() as c:
        return c.execute('SELECT question FROM questions WHERE guest_id=? ORDER BY id',(guest_id,)).fetchall()

def all_text(guest_id):
    return [x[0] for x in personal(guest_id)]

def global_count():
    with lock, connect() as c:
        return c.execute('SELECT COUNT(*) FROM questions').fetchone()[0]

def insert(guest_id,session_id,question,career,embedding=None):
    with lock,connect() as c:
        c.execute('INSERT INTO questions(guest_id,session_id,question,career,embedding) VALUES(?,?,?,?,?)',
                  (guest_id,session_id,question,career,json.dumps(embedding) if embedding else None))
