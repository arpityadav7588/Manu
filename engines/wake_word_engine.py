"""
engines/wake_word_engine.py
Always-on offline wake word detection.
Uses pvporcupine with the free built-in "porcupine" keyword,
mapped to respond to "Hey Manu" via a custom keyword file,
OR falls back to a lightweight Whisper-tiny loop.
"""

import struct
import threading
import logging
import time

log = logging.getLogger("Manu.WakeWord")


class WakeWordEngine:
    """
    Always-on background wake word detector.
    CPU usage: under 1% (Porcupine) or ~3% (Whisper fallback).
    Calls on_detected() callback when wake word is heard.
    """

    def __init__(self, on_detected_callback, wake_words=None):
        self.on_detected = on_detected_callback
        self.wake_words  = wake_words or ["hey manu", "manu", "hey star"]
        self._running    = False
        self._thread     = None
        self._engine     = None
        self._backend    = None
        self._select_backend()

    def _select_backend(self):
        """Choose the best available offline wake word backend."""
        # Try Porcupine first (most efficient)
        try:
            import pvporcupine
            key = self._get_porcupine_key()
            if key:
                # Use free built-in keyword "porcupine" as placeholder
                # For real "hey manu": get free key at console.picovoice.ai
                # then pass keyword_paths=["hey_manu.ppn"]
                self._porcupine = pvporcupine.create(
                    access_key=key,
                    keywords=["porcupine"],   # change to "hey manu" .ppn file
                )
                self._backend = "porcupine"
                log.info("Wake word backend: Porcupine (low CPU, offline)")
                return
            else:
                log.debug("No Porcupine key found, skipping backend.")
        except Exception as e:
            log.debug(f"Porcupine not available: {e}")

        # Fallback: Whisper-tiny streaming loop
        try:
            from faster_whisper import WhisperModel
            self._whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
            self._backend = "whisper"
            log.info("Wake word backend: Whisper-tiny (offline, ~3% CPU)")
            return
        except Exception as e:
            log.debug(f"Whisper not available (requires faster-whisper): {e}")

        # Last resort: SpeechRecognition + Google (needs internet)
        self._backend = "speech_recognition"
        log.warning("Wake word backend: SpeechRecognition (requires internet)")

    def _get_porcupine_key(self):
        """Load Porcupine access key from config or env."""
        import os
        # Set PORCUPINE_KEY environment variable, or put it in config.py
        key = os.environ.get("PORCUPINE_KEY", "")
        if not key:
            try:
                import config
                key = getattr(config, "PORCUPINE_KEY", "")
            except ImportError:
                pass
        return key

    def start(self):
        """Start background wake word listening thread."""
        self._running = True
        self._thread  = threading.Thread(
            target=self._listen_loop,
            name="WakeWordListener",
            daemon=True,          # Dies when main process exits
        )
        self._thread.start()
        log.info(f"Wake word listener started ({self._backend})")

    def stop(self):
        self._running = False

    def _listen_loop(self):
        """Background loop — calls on_detected() when wake word heard."""
        if self._backend == "porcupine":
            self._porcupine_loop()
        elif self._backend == "whisper":
            self._whisper_loop()
        else:
            self._sr_loop()

    # ── Porcupine Loop ──────────────────────────────────────────────────
    def _porcupine_loop(self):
        import pvrecorder
        recorder = pvrecorder.PvRecorder(
            frame_length=self._porcupine.frame_length
        )
        recorder.start()
        log.info("Porcupine recorder started. Listening silently...")

        try:
            while self._running:
                pcm = recorder.read()
                result = self._porcupine.process(pcm)
                if result >= 0:
                    log.info("Porcupine: wake word detected!")
                    self.on_detected()
                    time.sleep(1.0)  # Debounce
        except Exception as e:
            log.error(f"Porcupine loop error: {e}")
        finally:
            recorder.stop()
            recorder.delete()
            self._porcupine.delete()

    # ── Whisper-tiny Loop ────────────────────────────────────────────────
    def _whisper_loop(self):
        """Low-CPU Whisper-tiny loop for wake word detection."""
        import speech_recognition as sr
        import io, soundfile as sf

        recognizer = sr.Recognizer()
        recognizer.energy_threshold        = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold          = 0.5

        log.info("Whisper-tiny wake word loop started.")
        while self._running:
            try:
                with sr.Microphone() as source:
                    audio = recognizer.listen(
                        source, timeout=1.0, phrase_time_limit=3.0
                    )

                wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
                samples, _ = sf.read(io.BytesIO(wav_bytes), dtype="float32")

                segs, _ = self._whisper.transcribe(
                    samples, language="en", beam_size=1, vad_filter=True
                )
                text = " ".join(s.text for s in segs).strip().lower()

                if any(w in text for w in ["hey manu", "hey star", "manu"]):
                    log.info(f"Whisper wake word in: '{text}'")
                    self.on_detected()
                    time.sleep(1.0)

            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                log.debug(f"Whisper wake loop error (normal): {e}")
                time.sleep(0.2)

    # ── SpeechRecognition Fallback ────────────────────────────────────────
    def _sr_loop(self):
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300

        log.info("SpeechRecognition wake word loop started (Google fallback).")
        while self._running:
            try:
                with sr.Microphone() as source:
                    audio = recognizer.listen(
                        source, timeout=1.0, phrase_time_limit=3.0
                    )
                text = recognizer.recognize_google(audio).lower()
                if any(w in text for w in self.wake_words):
                    log.info(f"Google STT wake word in: '{text}'")
                    self.on_detected()
                    time.sleep(1.0)
            except Exception:
                time.sleep(0.3)
