"""
modules/memory_manager.py
Persistent SQLite memory for Manu.
Stores conversations, settings, reminders, session logs.
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from pathlib import Path

log = logging.getLogger("Manu.Memory")

DB_PATH = Path("data") / "manu.db"


class MemoryManager:

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        log.info(f"Memory store ready: {DB_PATH}")

    def _conn(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_text TEXT,
                    manu_text TEXT,
                    timestamp TEXT
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    title     TEXT,
                    remind_at TEXT,
                    notified  INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT,
                    ended_at   TEXT
                );
                CREATE TABLE IF NOT EXISTS security_log (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    event     TEXT,
                    timestamp TEXT
                );
            """)

    def log_interaction(self, user_text: str, manu_text: str):
        ts = datetime.now().isoformat()
        with self._conn() as c:
            c.execute(
                "INSERT INTO interactions (user_text, manu_text, timestamp) "
                "VALUES (?,?,?)",
                (user_text, manu_text, ts)
            )

    def get_recent(self, n: int = 8) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT user_text, manu_text, timestamp FROM interactions "
                "ORDER BY id DESC LIMIT ?", (n,)
            ).fetchall()
        return [
            {"user": r[0], "manu": r[1], "timestamp": r[2]}
            for r in reversed(rows)
        ]

    def get_last_session_summary(self) -> str:
        rows = self.get_recent(5)
        if not rows:
            return ""
        lines = [f"• {r['user']}" for r in rows]
        return "Recent: " + " | ".join(r['user'][:40] for r in rows)

    def get_setting(self, key: str, default=None):
        with self._conn() as c:
            row = c.execute(
                "SELECT value FROM settings WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return row[0]

    def set_setting(self, key: str, value):
        val = json.dumps(value) if not isinstance(value, str) else value
        with self._conn() as c:
            c.execute(
                "INSERT INTO settings (key,value) VALUES (?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, val)
            )

    def add_reminder(self, title: str, iso_datetime: str):
        with self._conn() as c:
            c.execute(
                "INSERT INTO reminders (title, remind_at) VALUES (?,?)",
                (title, iso_datetime)
            )
        log.info(f"Reminder set: '{title}' at {iso_datetime}")

    def get_due_reminders(self) -> list[dict]:
        now = datetime.now().isoformat()
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, title, remind_at FROM reminders "
                "WHERE notified=0 AND remind_at <= ?", (now,)
            ).fetchall()
        return [{"id": r[0], "title": r[1], "remind_at": r[2]} for r in rows]

    def mark_done(self, reminder_id: int):
        with self._conn() as c:
            c.execute(
                "UPDATE reminders SET notified=1 WHERE id=?", (reminder_id,)
            )

    def log_security_event(self, event: str):
        ts = datetime.now().isoformat()
        with self._conn() as c:
            c.execute(
                "INSERT INTO security_log (event, timestamp) VALUES (?,?)",
                (event, ts)
            )

    def build_llm_context(self, n: int = 6) -> str:
        rows = self.get_recent(n)
        if not rows:
            return ""
        parts = []
        for r in rows:
            parts.append(f"User: {r['user']}")
            parts.append(f"Manu: {r['manu']}")
        return "\n".join(parts)
