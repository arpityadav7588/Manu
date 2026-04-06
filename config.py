import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
CAPTURES_DIR = DATA_DIR / "captures"
DB_PATH = DATA_DIR / "manu.db"

# Ensure directories exist
for folder in [DATA_DIR, LOGS_DIR, CAPTURES_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Identity
MANU_NAME = "Manu"
USER_NAME = "arpit"  # Overwritten on setup

# Wake words
WAKE_WORDS = ["hey manu", "hey star", "manu"]

# STT (Speech to Text)
STT_ENGINE = "whisper"  # "whisper" or "google"
WHISPER_MODEL = "base"
ENERGY_THRESHOLD = 300
STT_LISTEN_TIMEOUT = 8
STT_PHRASE_LIMIT = 15

# TTS (Text to Speech)
TTS_ENGINE = "pyttsx3"
TTS_RATE = 175
TTS_VOLUME = 0.92
TTS_VOICE_ID = None

# LLM (Large Language Model)
LLM_ENGINE = "ollama"
LLM_MODEL = "llama3:8b"
OLLAMA_HOST = "http://localhost:11434"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 300
LLM_CONTEXT_MSGS = 10

# Security
SECURITY_ENABLED = True
PASSWORD_HASH = "8278abcc2dde637389bfab6e8bd218c4133e0e7ef73575a4981ca66359922c2c"  # Empty triggers setup wizard
MAX_AUTH_ATTEMPTS = 3
WEBCAM_ON_FAIL = True
SESSION_LOCK_CMD = "enter sleep mode"

# Battery
BATTERY_LOW_THRESHOLD = 20
BATTERY_FULL_THRESHOLD = 95
MONITOR_INTERVAL_SEC = 45

# Memory
MAX_MEMORY_ENTRIES = 2000
MEMORY_CONTEXT_LIMIT = 6

# GUI
GUI_ENABLED = True
GUI_WIDTH = 480
GUI_HEIGHT = 700
GUI_THEME = "dark"

# Emotion Emojis
EMOTION_EMOJIS = {
    "happy": "😊",
    "excited": "🤩",
    "concerned": "😟",
    "sleepy": "😴",
    "thinking": "🤔",
    "listening": "👂",
    "surprised": "😮",
    "grateful": "🙏",
    "playful": "😜",
    "neutral": "🙂",
    "error": "😵",
    "secure": "🔒"
}

# App Shortcuts
APP_SHORTCUTS = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "gmail": "https://mail.google.com",
    "notepad": "notepad",
    "calculator": "calc",
    "file explorer": "explorer",
    "task manager": "taskmgr",
    "settings": "ms-settings:",
    "paint": "mspaint"
}

AUTO_LOAD_SKILLS = True
