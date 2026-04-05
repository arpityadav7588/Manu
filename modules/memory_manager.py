import sqlite3
import json
import datetime
import os
from pathlib import Path
import config

class MemoryManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        self._init_db()

    def _init_db(self):
        """Create tables if they do not exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    summary TEXT
                )
            ''')
            
            # Reminders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    remind_at DATETIME,
                    notified INTEGER DEFAULT 0
                )
            ''')
            
            # Security log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT,
                    detail TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def log_interaction(self, role, msg):
        """INSERT into interactions table (role, message, timestamp)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interactions (role, message) VALUES (?, ?)",
                (role, msg)
            )
            # Maintain max entries
            cursor.execute(
                "DELETE FROM interactions WHERE id NOT IN (SELECT id FROM interactions ORDER BY id DESC LIMIT ?)",
                (config.MAX_MEMORY_ENTRIES,)
            )
            conn.commit()

    def get_recent_interactions(self, n):
        """SELECT last n rows, return list of dicts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, message, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
                (n,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    def get_last_interaction(self):
        """Return last user message string or None"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message FROM interactions WHERE role='user' ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def summarize_yesterday(self):
        """Return bullet string of yesterday's user messages"""
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message FROM interactions WHERE role='user' AND timestamp LIKE ? ORDER BY timestamp ASC",
                (f"{yesterday}%",)
            )
            rows = cursor.fetchall()
            if not rows:
                return "I don't recall any conversations from yesterday."
            
            summary = "\n".join([f"- {row[0]}" for row in rows])
            return f"Yesterday, we talked about:\n{summary}"

    def search_memory(self, keyword, n=5):
        """LIKE search, return list of dicts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, message, timestamp FROM interactions WHERE message LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{keyword}%", n)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_setting(self, key, default=None):
        """SELECT from settings table, JSON-decode value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return default

    def set_setting(self, key, value):
        """UPSERT into settings table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()

    def start_session(self):
        """INSERT into sessions table, return session id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sessions (started_at) VALUES (CURRENT_TIMESTAMP)")
            conn.commit()
            return cursor.lastrowid

    def end_session(self, session_id, summary):
        """UPDATE sessions set ended_at, summary"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET ended_at=CURRENT_TIMESTAMP, summary=? WHERE id=?",
                (summary, session_id)
            )
            conn.commit()

    def add_reminder(self, title, time_str):
        """INSERT into reminders table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (title, remind_at) VALUES (?, ?)",
                (title, time_str)
            )
            conn.commit()

    def get_due_reminders(self):
        """SELECT reminders where remind_at <= now and notified=0"""
        now = datetime.datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, remind_at FROM reminders WHERE remind_at <= ? AND notified=0",
                (now,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def mark_reminder_notified(self, reminder_id):
        """UPDATE reminders set notified=1"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET notified=1 WHERE id=?", (reminder_id,))
            conn.commit()

    def list_reminders(self):
        """SELECT all pending reminders"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, remind_at FROM reminders WHERE notified=0 ORDER BY remind_at ASC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def log_security_event(self, event, detail):
        """INSERT into security_log table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO security_log (event, detail) VALUES (?, ?)",
                (event, detail)
            )
            conn.commit()

    def build_llm_context(self, limit):
        """Return list of {role, content} dicts for LLM injection"""
        interactions = self.get_recent_interactions(limit)
        context = []
        for interact in interactions:
            role = "assistant" if interact['role'] == "manu" else interact['role']
            context.append({"role": role, "content": interact['message']})
        return context
