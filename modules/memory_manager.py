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
                    tags TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Voice notes table (Task 3a)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

            # Habits table (Task 3a)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE,
                    frequency TEXT,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    count INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            
            # Check tables for confirmation print
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            print(f"[*] Memory: SQLite database connected. {len(tables)} tables ready.")

    def log_interaction(self, user_text, manu_text):
        """INSERT both user and manu messages into interactions table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Log user message
            cursor.execute(
                "INSERT INTO interactions (role, message) VALUES (?, ?)",
                ("user", user_text)
            )
            # Log manu message
            cursor.execute(
                "INSERT INTO interactions (role, message) VALUES (?, ?)",
                ("manu", manu_text)
            )
            # Maintain max entries
            cursor.execute(
                "DELETE FROM interactions WHERE id NOT IN (SELECT id FROM interactions ORDER BY id DESC LIMIT ?)",
                (config.MAX_MEMORY_ENTRIES,)
            )
            conn.commit()

    def get_recent(self, limit=10):
        """SELECT last n rows, return list of dicts"""
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
        """Return last user message string or None"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message FROM interactions WHERE role='user' ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def search(self, keyword, limit=5):
        """LIKE search, return list of dicts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, message, timestamp FROM interactions WHERE message LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{keyword}%", limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

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

    def get_setting(self, key, default=None):
        """SELECT from settings table, JSON-decode value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0] # Fallback for non-JSON strings
            return default

    def set_setting(self, key, value):
        """UPSERT into settings table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            val_to_save = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, val_to_save)
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

    def add_reminder(self, title, remind_at_iso):
        """INSERT into reminders table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (title, remind_at) VALUES (?, ?)",
                (title, remind_at_iso)
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

    def mark_reminder_done(self, reminder_id):
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

    def build_personality_context(self):
        """Construct a personality brief for LLM injection."""
        habits = self.get_top_habits(3)
        habit_str = ", ".join([h['pattern'] for h in habits]) if habits else "None yet"
        user_name = self.get_setting("user_name", config.USER_NAME)
        
        context = (
            f"User Identity: {user_name}. "
            f"Frequent User Habits/Topics: {habit_str}. "
            "Your personality: Warm, professional, slightly witty."
        )
        return context

    def summarize_last_session(self):
        """Retrieve and return a brief summary of the last session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT summary FROM sessions WHERE summary IS NOT NULL ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else "No previous sessions found."

    def build_llm_context(self, limit=8):
        """Return list of {role, content} dicts for LLM injection"""
        interactions = self.get_recent(limit)
        context = []
        for interact in interactions:
            role = "assistant" if interact['role'] == "manu" else interact['role']
            context.append({"role": role, "content": interact['message']})
        return context
