"""Check existing DB schema and fix column mismatch."""
import sqlite3
import os

DB = "data/manu.db"

if not os.path.exists(DB):
    print("No DB found - will be created fresh on next run.")
    exit(0)

c = sqlite3.connect(DB)

print("=== Current tables ===")
for row in c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
    print(f"\n{row[0]}:")
    print(f"  {row[1]}")

# Check if interactions table has the right columns
try:
    cursor = c.execute("PRAGMA table_info(interactions)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"\ninteractions columns: {cols}")
    
    if "user_text" not in cols:
        print("\n!!! Column mismatch: 'user_text' not found")
        print("    Existing columns:", cols)
        
        # Rename old table and create new one
        print("\n--- Migrating interactions table ---")
        c.execute("ALTER TABLE interactions RENAME TO interactions_old")
        c.execute("""
            CREATE TABLE interactions (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_text TEXT,
                manu_text TEXT,
                timestamp TEXT
            )
        """)
        
        # Try to migrate old data based on likely column names
        old_cols = cols
        if "role" in old_cols and "content" in old_cols:
            # Siri-mode schema: role, content, timestamp
            print("  Migrating from role/content schema...")
            rows = c.execute("SELECT role, content, timestamp FROM interactions_old").fetchall()
            for role, content, ts in rows:
                if role == "user":
                    c.execute("INSERT INTO interactions (user_text, manu_text, timestamp) VALUES (?,?,?)",
                              (content, "", ts))
                else:
                    c.execute("INSERT INTO interactions (user_text, manu_text, timestamp) VALUES (?,?,?)",
                              ("", content, ts))
        elif "query" in old_cols and "response" in old_cols:
            print("  Migrating from query/response schema...")
            rows = c.execute("SELECT query, response, timestamp FROM interactions_old").fetchall()
            for q, r, ts in rows:
                c.execute("INSERT INTO interactions (user_text, manu_text, timestamp) VALUES (?,?,?)",
                          (q or "", r or "", ts))
        else:
            print("  Unknown old schema - starting fresh")
        
        c.execute("DROP TABLE interactions_old")
        c.commit()
        print("  Migration complete!")
    else:
        print("\n  Schema is correct - no migration needed")
        
except Exception as e:
    print(f"Error: {e}")

# Ensure all required tables exist
print("\n--- Ensuring all required tables ---")
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
c.commit()

# Verify final state
print("\n=== Final schema ===")
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({row[0]})").fetchall()]
    print(f"  {row[0]}: {cols}")

c.close()
print("\nDone!")
