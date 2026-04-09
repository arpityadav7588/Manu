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
        """Create tables if they do not exist (Upgrade 3)."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Interactions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT,
                    message TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Reminders
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    remind_at TEXT,
                    notified INTEGER DEFAULT 0
                )
            ''')
            
            # Security Log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT,
                    detail TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print(f"[*] Memory: SQLite DB ready at {self.db_path}")

    def log_interaction(self, role, message):
        """Insert into interactions (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interactions (role, message) VALUES (?, ?)",
                (role, message)
            )
            conn.commit()

    def get_recent(self, limit=10):
        """Select last N interactions (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, message, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    def get_last_user_message(self):
        """Return last user message or None (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message FROM interactions WHERE role='user' ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def build_llm_context(self, limit=6):
        """OpenAI-style message list (Upgrade 3)."""
        recent = self.get_recent(limit)
        context = []
        for r in recent:
            # Map 'manu' or 'assistant' to assistant role
            role = "assistant" if r['role'] in ["manu", "assistant"] else "user"
            context.append({"role": role, "content": r['message']})
        return context

    def set_setting(self, key, value):
        """UPSERT into settings (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            val_str = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, val_str)
            )
            conn.commit()

    def get_setting(self, key, default=None):
        """Select from settings (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
            return default

    def add_reminder(self, title, remind_at_iso_str):
        """Insert into reminders (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (title, remind_at) VALUES (?, ?)",
                (title, remind_at_iso_str)
            )
            conn.commit()

    def get_due_reminders(self):
        """Select due reminders (Upgrade 3)."""
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

    def mark_reminder_done(self, reminder_id):
        """Set notified=1 (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET notified=1 WHERE id=?", (reminder_id,))
            conn.commit()

    def log_security(self, event, detail):
        """Insert into security_log (Upgrade 3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO security_log (event, detail) VALUES (?, ?)",
                (event, detail)
            )
            conn.commit()

    def summarize_yesterday(self):
        """Bullet summary of yesterday's conversations (Upgrade 3)."""
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
            
            lines = [f"• {r[0]}" for r in rows]
            return f"Yesterday we discussed:\n" + "\n".join(lines)
