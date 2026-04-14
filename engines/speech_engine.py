"""
engines/speech_engine.py
Offline text-to-speech for Manu using pyttsx3.
No internet required. Works on Windows, Linux, Mac.
"""

import pyttsx3
import threading
import logging
import time

log = logging.getLogger("Manu.Speech")


class SpeechEngine:
    """
    Offline TTS engine. Wraps pyttsx3 with:
      - Auto voice selection (prefers male English voice)
      - Emotion-driven rate/volume modulation
      - Thread-safe speak() with lock
      - Async non-blocking speak_async()
      - Graceful crash recovery
    """

    DEFAULT_RATE   = 175   # words per minute
    DEFAULT_VOLUME = 0.9   # 0.0 to 1.0

    def __init__(self):
        self._lock    = threading.Lock()
        self._engine  = None
        self._rate    = self.DEFAULT_RATE
        self._volume  = self.DEFAULT_VOLUME
        self._speaking = False
        self._init_engine()

    def _init_engine(self):
        """Initialize pyttsx3 and select best available male voice."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate",   self._rate)
            self._engine.setProperty("volume", self._volume)
            self._select_voice()
            log.info("SpeechEngine ready (pyttsx3, offline)")
        except Exception as e:
            log.error(f"SpeechEngine init failed: {e}")
            self._engine = None

    def _select_voice(self):
        """Auto-select the best male English voice available."""
        if not self._engine:
            return
        voices = self._engine.getProperty("voices")
        if not voices:
            return

        # Priority order: prefer deep/male voices by name keyword
        preferred_keywords = [
            "david", "mark", "george", "james", "daniel",
            "male", "man", "guy", "english"
        ]
        selected = None

        for keyword in preferred_keywords:
            for v in voices:
                name_lower = v.name.lower()
                if keyword in name_lower:
                    selected = v
                    break
            if selected:
                break

        # Fallback: just use first voice
        if not selected and voices:
            selected = voices[0]

        if selected:
            self._engine.setProperty("voice", selected.id)
            log.info(f"Voice selected: {selected.name}")

    def speak(self, text: str, rate: int = None, volume: float = None):
        """
        Speak text aloud. Blocks until speech is complete.
        Temporarily overrides rate/volume if provided.
        Also prints to console for debugging.
        """
        if not text or not text.strip():
            return
        if not self._engine:
            print(f"[Manu - no TTS]: {text}")
            return

        # Console output always (useful for debugging)
        print(f"\n🔊 Manu: {text}\n")
        log.info(f"Speaking: {text[:70]}{'...' if len(text)>70 else ''}")

        with self._lock:
            self._speaking = True
            try:
                # Apply temporary overrides if given
                if rate is not None:
                    self._engine.setProperty("rate", rate)
                if volume is not None:
                    self._engine.setProperty("volume", volume)

                self._engine.say(text)
                self._engine.runAndWait()

            except RuntimeError as e:
                # pyttsx3 can enter bad state on Windows — reinit and retry
                log.warning(f"TTS RuntimeError: {e} — reinitializing engine")
                try:
                    self._init_engine()
                    if self._engine:
                        self._engine.say(text)
                        self._engine.runAndWait()
                except Exception as retry_err:
                    log.error(f"TTS retry failed: {retry_err}")

            except Exception as e:
                log.error(f"TTS speak error: {e}")

            finally:
                # Restore permanent rate/volume after temporary override
                if rate is not None and self._engine:
                    self._engine.setProperty("rate",   self._rate)
                if volume is not None and self._engine:
                    self._engine.setProperty("volume", self._volume)
                self._speaking = False

    def speak_async(self, text: str, rate: int = None, volume: float = None):
        """
        Non-blocking speak. Runs speak() in a background daemon thread.
        Use for proactive alerts that should not block the main loop.
        """
        thread = threading.Thread(
            target=self.speak,
            args=(text,),
            kwargs={"rate": rate, "volume": volume},
            daemon=True,
            name="ManuSpeak"
        )
        thread.start()

    def set_rate(self, rate: int):
        """Permanently change speaking rate (words per minute)."""
        self._rate = max(100, min(400, rate))
        if self._engine:
            self._engine.setProperty("rate", self._rate)
        log.debug(f"TTS rate set to {self._rate}")

    def set_volume(self, volume: float):
        """Permanently change volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        if self._engine:
            self._engine.setProperty("volume", self._volume)
        log.debug(f"TTS volume set to {self._volume}")

    def apply_mood(self, mood: str):
        """
        Adjust voice parameters based on emotional state.
        Called by EmotionManager when mood changes.
        """
        mood_params = {
            "enthusiastic": {"rate": 195, "volume": 0.95},
            "happy":        {"rate": 185, "volume": 0.92},
            "neutral":      {"rate": 175, "volume": 0.90},
            "concerned":    {"rate": 155, "volume": 0.80},
            "sleepy":       {"rate": 140, "volume": 0.75},
            "playful":      {"rate": 190, "volume": 0.93},
            "grateful":     {"rate": 168, "volume": 0.88},
        }
        params = mood_params.get(mood, mood_params["neutral"])
        self.set_rate(params["rate"])
        self.set_volume(params["volume"])
        log.debug(f"TTS mood applied: {mood} → {params}")

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    @property
    def is_available(self) -> bool:
        return self._engine is not None
