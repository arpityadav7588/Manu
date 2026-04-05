import sqlite3
import os
import datetime

class MemoryManager:
    def __init__(self, db_path="data/manu_memory.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                response TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_habits (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_interaction(self, user_input, response):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO interactions (timestamp, user_input, response) VALUES (?, ?, ?)',
                       (datetime.datetime.now().isoformat(), user_input, response))
        conn.commit()
        conn.close()

    def update_habit(self, key, value):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO user_habits (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

    def get_habit(self, key):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM user_habits WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_recent_history(self, limit=5):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_input, response FROM interactions ORDER BY timestamp DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results

if __name__ == "__main__":
    memory = MemoryManager()
    memory.log_interaction("Hello", "Hi there!")
    print(memory.get_recent_history())
