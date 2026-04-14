"""
engines/tts_engine.py
Offline TTS using pyttsx3. No internet required.
Auto-selects the best male English voice.
"""

import pyttsx3
import threading
import logging
import config

log = logging.getLogger("Manu.TTS")


class TTSEngine:
    def __init__(self):
        self._engine = pyttsx3.init()
        self._lock   = threading.Lock()
        self._rate   = getattr(config, "TTS_RATE", 175)
        self._volume = getattr(config, "TTS_VOLUME", 0.9)
        self._setup_voice()
        log.info("TTS engine ready (pyttsx3, offline)")

    def _setup_voice(self):
        self._engine.setProperty("rate",   self._rate)
        self._engine.setProperty("volume", self._volume)
        voices = self._engine.getProperty("voices")
        for v in voices:
            if any(k in v.name.lower() for k in ["david", "mark", "george", "male"]):
                self._engine.setProperty("voice", v.id)
                log.info(f"Voice selected: {v.name}")
                return
        if voices:
            self._engine.setProperty("voice", voices[0].id)

    def speak(self, text: str, quick: bool = False):
        if not text or not text.strip():
            return
        try:
            print(f"\n[Manu]: {text}\n")
        except UnicodeEncodeError:
            print(f"\n[Manu]: {text.encode('ascii', 'ignore').decode('ascii')}\n")
        log.info(f"TTS: {text[:80]}")
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except RuntimeError:
                self._engine = pyttsx3.init()
                self._setup_voice()
                self._engine.say(text)
                self._engine.runAndWait()

    def speak_async(self, text: str):
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()

    def set_voice_params(self, rate=None, volume=None):
        if rate:
            self._rate = rate
            self._engine.setProperty("rate", rate)
        if volume:
            self._volume = volume
            self._engine.setProperty("volume", volume)
