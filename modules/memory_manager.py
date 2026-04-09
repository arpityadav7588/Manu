import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

class MemoryManager:
    def __init__(self):
        try:
            Path("./data").mkdir(parents=True, exist_ok=True)
            self.db_path = "./data/manu.db"
            self._init_db()
        except Exception as e:
            print(f"Memory init error: {e}")

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS interactions(id INTEGER PRIMARY KEY, role TEXT, message TEXT, timestamp TEXT)")
                conn.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
                conn.execute("CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, title TEXT, remind_at TEXT, notified INTEGER DEFAULT 0)")
        except Exception as e:
            print(f"DB init error: {e}")

    def log_interaction(self, user_text: str, manu_response: str):
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO interactions (role, message, timestamp) VALUES (?, ?, ?)", ("user", user_text, now))
                conn.execute("INSERT INTO interactions (role, message, timestamp) VALUES (?, ?, ?)", ("manu", manu_response, now))
        except Exception as e:
            pass

    def get_recent(self, limit=8) -> list[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT role, message FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
                results = [{"role": row[0], "message": row[1]} for row in cursor.fetchall()]
                return results[::-1]
        except Exception as e:
            return []

    def get_last_user_message(self) -> str | None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT message FROM interactions WHERE role='user' ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            return None

    def summarize_yesterday(self) -> str:
        try:
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT message FROM interactions WHERE role='user' AND date(timestamp) = ?", (yesterday,))
                messages = [row[0] for row in cursor.fetchall()]
                if not messages:
                    return "No activity found from yesterday."
                return "- " + "\n- ".join(messages)
        except Exception as e:
            return "No activity found from yesterday."

    def get_setting(self, key, default=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT value FROM settings WHERE key=?", (key,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return default
        except Exception as e:
            return default

    def set_setting(self, key, value):
        try:
            val_str = json.dumps(value)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, val_str))
        except Exception as e:
            pass

    def add_reminder(self, title: str, remind_at: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO reminders (title, remind_at) VALUES (?, ?)", (title, remind_at))
        except Exception as e:
            pass

    def get_due_reminders(self) -> list[dict]:
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT id, title, remind_at FROM reminders WHERE notified=0 AND remind_at <= ?", (now,))
                return [{"id": row[0], "title": row[1], "remind_at": row[2]} for row in cursor.fetchall()]
        except Exception as e:
            return []

    def mark_notified(self, reminder_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE reminders SET notified=1 WHERE id=?", (reminder_id,))
        except Exception as e:
            pass
