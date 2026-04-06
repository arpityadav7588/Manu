import sys
import os
import sqlite3
import datetime
from pathlib import Path

def check_imports():
    print("--- Checking Dependencies ---")
    libs = [
        "pywebview", "websockets", "openwakeword", "psutil", 
        "pyperclip", "PIL", "cv2", "ollama", "requests", "faster_whisper"
    ]
    for lib in libs:
        try:
            if lib == "pywebview": import webview
            elif lib == "PIL": from PIL import Image
            else: __import__(lib)
            print(f"[*] {lib} is installed.")
        except ImportError:
            print(f"[X] {lib} is MISSING.")

def check_db():
    print("\n--- Checking SQLite Database ---")
    db_path = Path("d:/manu/Manu/data/manu.db")
    if not db_path.exists():
        print(f"[X] Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"[*] Database connected. Tables: {', '.join(tables)}")
        conn.close()
    except Exception as e:
        print(f"[X] Database error: {e}")

def check_folders():
    print("\n--- Checking Data Folders ---")
    folders = ["data/notes", "data/screenshots", "data/captures"]
    for f in folders:
        path = Path("d:/manu/Manu") / f
        if path.exists():
            print(f"[*] {f} exists.")
        else:
            print(f"[X] {f} is MISSING.")

if __name__ == "__main__":
    check_imports()
    check_folders()
    check_db()
