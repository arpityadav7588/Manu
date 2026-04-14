# Manu — Local AI Assistant · Setup Guide

## Quick Start

```bash
# 1. Install core dependencies (required)
pip install pyttsx3 SpeechRecognition pyaudio psutil requests pillow customtkinter

# 2. Install offline STT (strongly recommended)
pip install faster-whisper soundfile

# 3. Run Manu
python main.py
```

## Install Ollama (for full intelligence)

1. Download from https://ollama.com
2. Run: `ollama serve`
3. Run: `ollama pull llama3.2`
4. Restart Manu

Without Ollama, Manu runs in fallback mode with rule-based responses.
All system commands (battery, apps, volume, etc.) still work fully offline.

## Optional Features

```bash
# Webcam security capture on failed auth
pip install opencv-python

# Clipboard reading
pip install pyperclip

# Windows precision volume control
pip install pycaw comtypes

# Brightness control
pip install screen-brightness-control
```

## Test Manu Works

Say: **"Hey Manu"**  
Then try:
1. `"What time is it?"` → Should tell you the time
2. `"Tell me a joke"` → Should crack a joke
3. `"Open YouTube"` → Should open youtube.com in browser
4. `"Check battery"` → Should report battery status
5. `"What's my CPU usage?"` → Should report system info

If all 5 work, **Phase 1 is complete** ✅

## Architecture

| File | Role |
|------|------|
| `engines/speech_engine.py` | Text-to-speech (pyttsx3, offline) |
| `engines/audio_engine.py` | Speech-to-text (faster-whisper, offline) |
| `engines/brain_engine.py` | LLM brain (Ollama + fallback) |
| `engines/command_engine.py` | Command dispatcher (20+ commands) |
| `modules/memory_manager.py` | SQLite persistent memory |
| `modules/emotion_manager.py` | Mood state machine |
| `modules/security_manager.py` | Auth + webcam security |
| `modules/system_monitor.py` | Battery + internet monitor |

## Troubleshooting

**PyAudio install fails on Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**pyttsx3 no sound on Windows:**  
Make sure Windows TTS service is enabled. Run `spx` or check `Services → Windows Audio`.

**Whisper model too slow:**  
Use `tiny` model: edit `audio_engine.py` and change `model="base"` → `model="tiny"`.

**Ollama model not found:**  
Run `ollama list` to see installed models. Run `ollama pull llama3.2` to download.
