"""
engines/audio_engine.py
Offline speech-to-text for Manu.
Primary:  faster-whisper (local, no internet, accurate)
Fallback: SpeechRecognition + Google (needs internet)
"""

import io
import logging
import time
import threading

import speech_recognition as sr

log = logging.getLogger("Manu.Audio")


class AudioEngine:
    """
    Offline STT using faster-whisper.
    Falls back to Google STT if faster-whisper is not installed.

    Key methods:
      listen_and_recognize()  — one shot: listen + transcribe
      listen_for_wake_word()  — blocking loop, returns True on "hey manu"
      calibrate()             — adjust mic for ambient noise
    """

    WAKE_WORDS = ["hey manu", "hey star", "manu", "hey man"]

    def __init__(self, model: str = "base"):
        self._model_size = model
        self._whisper = None  # Main command model
        self._wake_whisper = None  # Tiny model for wake word (faster)
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = 300
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.8
        self._google_fallback = False

        self._load_whisper()

    # ── Model Loading ─────────────────────────────────────────────────────────
    def _load_whisper(self):
        """Load faster-whisper model. Falls back to Google STT if missing."""
        try:
            from faster_whisper import WhisperModel

            log.info(f"Loading faster-whisper '{self._model_size}' model...")
            self._whisper = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",   # int8 = fastest on CPU, minimal quality loss
            )
            log.info(f"faster-whisper '{self._model_size}' loaded ✅ (offline STT ready)")

        except ImportError:
            log.warning(
                "faster-whisper not installed — falling back to Google STT.\n"
                "  For offline mode: pip install faster-whisper soundfile"
            )
            self._google_fallback = True

        except Exception as e:
            log.error(f"Whisper load failed: {e}. Using Google STT fallback.")
            self._google_fallback = True

    def _load_wake_whisper(self):
        """
        Lazily load 'tiny' Whisper model for wake word detection.
        Separate from command model to keep wake detection fast.
        """
        if self._wake_whisper is not None:
            return
        if self._google_fallback:
            return
        try:
            from faster_whisper import WhisperModel
            log.info("Loading wake-word Whisper (tiny) model...")
            self._wake_whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
            log.info("Wake-word Whisper (tiny) loaded ✅")
        except Exception as e:
            log.warning(f"Wake-word tiny model failed: {e}")
            self._wake_whisper = self._whisper  # Use base as fallback

    # ── Calibration ───────────────────────────────────────────────────────────
    def calibrate(self, duration: float = 1.5):
        """
        Adjust microphone sensitivity for current ambient noise.
        Call once at startup before listening begins.
        """
        log.info(f"Calibrating microphone for {duration}s ambient noise...")
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)
            log.info(
                f"Mic calibrated. Energy threshold: "
                f"{self._recognizer.energy_threshold:.0f}"
            )
        except Exception as e:
            log.error(f"Microphone calibration failed: {e}")

    # ── Main Listen + Transcribe ──────────────────────────────────────────────
    def listen_and_recognize(
        self,
        timeout: int = 8,
        phrase_limit: int = 15
    ) -> str | None:
        """
        Open microphone, wait for speech, transcribe and return text.
        Returns None if nothing was heard or transcription failed.
        """
        try:
            with sr.Microphone() as source:
                # Quick ambient adjustment each listen for accuracy
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                log.debug("Microphone open — listening for command...")

                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit,
                )

            # Transcribe the captured audio
            text = self._transcribe(audio, model="command")
            if text:
                log.info(f"Heard: '{text}'")
            return text

        except sr.WaitTimeoutError:
            log.debug("Listen timeout — no speech detected.")
            return None
        except sr.UnknownValueError:
            log.debug("Audio captured but could not understand.")
            return None
        except Exception as e:
            log.error(f"listen_and_recognize error: {e}")
            return None

    # ── Wake Word Detection ───────────────────────────────────────────────────
    def listen_for_wake_word(self) -> bool:
        """
        Blocking loop: continuously listens in short bursts.
        Returns True the moment a wake word is detected.
        Designed to run in a background daemon thread.
        """
        # Lazily load tiny model for efficient wake detection
        self._load_wake_whisper()

        log.info(f"Wake word listener active. Listening for: {self.WAKE_WORDS}")

        while True:
            text = self._listen_short_burst()
            if text and self._is_wake_word(text):
                log.info(f"Wake word detected in: '{text}'")
                return True
            time.sleep(0.05)  # Tiny gap to prevent CPU spin

    def _listen_short_burst(self) -> str | None:
        """
        Listen for 3 seconds max. Used for wake word polling.
        Short bursts = responsive detection + low CPU.
        """
        try:
            with sr.Microphone() as source:
                audio = self._recognizer.listen(
                    source,
                    timeout=1.0,
                    phrase_time_limit=3.0,
                )
            return self._transcribe(audio, model="wake")
        except sr.WaitTimeoutError:
            return None
        except Exception:
            return None

    def _is_wake_word(self, text: str) -> bool:
        """Check if transcribed text contains any wake word."""
        text_lower = text.lower().strip()
        return any(wake in text_lower for wake in self.WAKE_WORDS)

    # ── Transcription ─────────────────────────────────────────────────────────
    def _transcribe(self, audio: sr.AudioData, model: str = "command") -> str | None:
        """Route audio to appropriate transcription backend."""
        if self._google_fallback:
            return self._google_transcribe(audio)
        return self._whisper_transcribe(audio, model=model)

    def _whisper_transcribe(
        self,
        audio: sr.AudioData,
        model: str = "command"
    ) -> str | None:
        """
        Transcribe using local faster-whisper model.
        model="wake" uses tiny model (fast).
        model="command" uses base model (accurate).
        """
        try:
            import soundfile as sf
            import numpy as np

            # Convert AudioData → numpy float32 at 16kHz (Whisper requirement)
            wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
            wav_io = io.BytesIO(wav_bytes)
            samples, sample_rate = sf.read(wav_io, dtype="float32")

            # Choose model
            whisper_model = (
                self._wake_whisper
                if model == "wake" and self._wake_whisper
                else self._whisper
            )

            if whisper_model is None:
                return self._google_transcribe(audio)

            # Transcribe
            segments, info = whisper_model.transcribe(
                samples,
                language="en",
                beam_size=5 if model == "command" else 1,
                vad_filter=True,       # Skip silence segments
                vad_parameters=dict(
                    min_silence_duration_ms=300
                ),
            )

            text = " ".join(segment.text for segment in segments).strip()
            return text if text else None

        except ImportError as e:
            log.warning(f"soundfile missing: {e}. Falling back to Google STT.")
            self._google_fallback = True
            return self._google_transcribe(audio)

        except Exception as e:
            log.error(f"Whisper transcribe error: {e}")
            return self._google_transcribe(audio)

    def _google_transcribe(self, audio: sr.AudioData) -> str | None:
        """
        Fallback: Google Web Speech API.
        Requires internet. Used when faster-whisper is not installed.
        """
        try:
            text = self._recognizer.recognize_google(
                audio,
                language="en-IN"   # Indian English accent support
            )
            log.debug(f"Google STT: '{text}'")
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            log.error(f"Google STT request failed (no internet?): {e}")
            return None
        except Exception as e:
            log.error(f"Google STT error: {e}")
            return None

    # ── Utility ───────────────────────────────────────────────────────────────
    @property
    def is_offline(self) -> bool:
        """True if using local Whisper (no internet needed)."""
        return not self._google_fallback

    @property
    def model_info(self) -> str:
        """Human-readable description of active STT backend."""
        if self._google_fallback:
            return "Google STT (online fallback)"
        return f"faster-whisper '{self._model_size}' (offline)"
