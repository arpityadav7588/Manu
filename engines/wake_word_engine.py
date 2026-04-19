"""
engines/wake_word_engine.py
Always-on offline wake word detection for Manu.

Strategy: Listen in short 3-second bursts using Whisper-tiny.
Whisper-tiny is fast enough to run on CPU at ~2-3% load.
No internet. No API key. No cloud.

When "hey manu", "hey star", or "manu" is heard in a burst,
calls the on_detected callback immediately.

CPU profile (tested on i5, base model):
  Wake detection (tiny):  ~2-3% CPU
  Command recognition (base): spikes to ~40% for 1-2 seconds then drops
"""

import io
import logging
import threading
import time

import speech_recognition as sr

log = logging.getLogger("Manu.WakeWord")

WAKE_WORDS = [
    "hey manu", "hey man", "hey star", "manu",
    "a manu", "hey menu",           # common mishears
]


class WakeWordEngine:
    """
    Always-on background wake word detector.
    Uses Whisper-tiny for efficient local transcription.

    Usage:
        engine = WakeWordEngine(on_detected=my_callback)
        engine.start()   # non-blocking, runs in daemon thread
        engine.stop()    # call to shut down
        engine.pause()   # call while processing a command
        engine.resume()  # call when ready to listen again
    """

    def __init__(self, on_detected):
        """
        on_detected: callable with no arguments.
        Called from background thread when wake word is heard.
        """
        self._on_detected = on_detected
        self._running     = False
        self._paused      = False
        self._thread      = None

        # Whisper-tiny model (lazy loaded on first start)
        self._tiny_model  = None
        self._model_lock  = threading.Lock()
        self._model_ready = False

        # SpeechRecognition for mic capture
        self._recognizer  = sr.Recognizer()
        self._recognizer.energy_threshold         = 250
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold          = 0.6

        log.info(f"WakeWordEngine created. Keywords: {WAKE_WORDS}")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """Start background wake word listener. Non-blocking."""
        self._running = True
        self._thread  = threading.Thread(
            target=self._startup_and_listen,
            name="WakeWordListener",
            daemon=True,          # Automatically dies when main process exits
        )
        self._thread.start()
        log.info("Wake word listener thread started.")

    def stop(self):
        """Stop the listener permanently."""
        self._running = False
        log.info("Wake word listener stopped.")

    def pause(self):
        """
        Pause detection while Manu is processing a command.
        Prevents double-triggering if user's command contains "manu".
        """
        self._paused = True

    def resume(self):
        """Resume detection after command processing is complete."""
        self._paused = False

    @property
    def is_ready(self) -> bool:
        """True once Whisper-tiny model is loaded."""
        return self._model_ready

    # ── Model Loading ─────────────────────────────────────────────────────────

    def _startup_and_listen(self):
        """Load Whisper-tiny then immediately start listening."""
        self._load_tiny_model()
        self._listen_loop()

    def _load_tiny_model(self):
        """Load faster-whisper tiny model (once, at startup)."""
        with self._model_lock:
            if self._tiny_model is not None:
                return
            try:
                from faster_whisper import WhisperModel
                log.info("Loading Whisper-tiny for wake word detection...")
                self._tiny_model = WhisperModel(
                    "tiny",
                    device="cpu",
                    compute_type="int8",   # Fastest, minimal quality loss
                )
                self._model_ready = True
                log.info("Whisper-tiny loaded ✅  Wake detection active.")
            except ImportError:
                log.error(
                    "faster-whisper not installed!\n"
                    "  Run: pip install faster-whisper soundfile\n"
                    "  Wake word detection will NOT work without it."
                )
                self._tiny_model  = None
                self._model_ready = False
            except Exception as e:
                log.error(f"Whisper-tiny load failed: {e}")
                self._tiny_model  = None
                self._model_ready = False

    # ── Main Listen Loop ──────────────────────────────────────────────────────

    def _listen_loop(self):
        """
        Core loop: listen in 3-second bursts → transcribe → check → repeat.
        Runs until self._running is False.
        """
        log.info("Wake word listen loop running. Say 'Hey Manu' anytime.")

        while self._running:
            # Skip while paused (command being processed)
            if self._paused:
                time.sleep(0.1)
                continue

            # Skip if model failed to load
            if not self._model_ready:
                time.sleep(1.0)
                continue

            try:
                # Capture short audio burst
                audio = self._capture_burst(timeout=1.0, phrase_limit=3.5)
                if audio is None:
                    continue

                # Transcribe with tiny model (fast)
                text = self._transcribe_tiny(audio)
                if text is None:
                    continue

                log.debug(f"Wake burst: '{text}'")

                # Check for wake word match
                if self._matches_wake_word(text):
                    log.info(f"✅ Wake word detected: '{text}'")
                    self._paused = True    # Stop listening immediately
                    try:
                        self._on_detected()
                    except Exception as cb_err:
                        log.error(f"Wake callback error: {cb_err}")
                    finally:
                        self._paused = False  # Resume after callback

            except Exception as e:
                log.debug(f"Wake loop iteration error (usually OK): {e}")
                time.sleep(0.2)

    # ── Audio Capture ─────────────────────────────────────────────────────────

    def _capture_burst(
        self,
        timeout: float = 1.0,
        phrase_limit: float = 3.5
    ) -> sr.AudioData | None:
        """
        Open mic and capture one short burst of audio.
        Returns AudioData or None if nothing heard.
        Short bursts (3s) keep response time fast.
        """
        try:
            with sr.Microphone() as source:
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit,
                )
            return audio
        except sr.WaitTimeoutError:
            return None   # Silence — completely normal, loop again
        except OSError as e:
            log.warning(f"Microphone not available: {e}")
            time.sleep(2.0)
            return None
        except Exception as e:
            log.debug(f"Burst capture error: {e}")
            return None

    # ── Transcription ─────────────────────────────────────────────────────────

    def _transcribe_tiny(self, audio: sr.AudioData) -> str | None:
        """
        Transcribe audio burst using Whisper-tiny.
        Returns lowercase string or None.
        Tiny model is ~39MB and processes 3s audio in ~0.3s on CPU.
        """
        if self._tiny_model is None:
            return None

        try:
            import soundfile as sf
            import numpy as np

            # Convert AudioData → numpy float32 at 16kHz (Whisper requirement)
            wav_bytes       = audio.get_wav_data(convert_rate=16000, convert_width=2)
            wav_io          = io.BytesIO(wav_bytes)
            samples, rate   = sf.read(wav_io, dtype="float32")

            # Ensure mono
            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            # Transcribe — beam_size=1 is fastest for tiny model
            segments, _ = self._tiny_model.transcribe(
                samples,
                language="en",
                beam_size=1,
                vad_filter=True,
                vad_parameters=dict(
                    threshold=0.5,
                    min_silence_duration_ms=200,
                    speech_pad_ms=100,
                ),
            )

            text = " ".join(seg.text for seg in segments).strip().lower()
            return text if text else None

        except ImportError:
            log.error("soundfile not installed. Run: pip install soundfile")
            return None
        except Exception as e:
            log.debug(f"Tiny transcribe error: {e}")
            return None

    # ── Wake Word Matching ────────────────────────────────────────────────────

    def _matches_wake_word(self, text: str) -> bool:
        """
        Check if transcribed text contains a wake word.
        Uses substring matching to handle surrounding words:
        "okay hey manu open youtube" → still triggers.
        """
        text_clean = text.lower().strip()
        return any(wake in text_clean for wake in WAKE_WORDS)
