"""
engines/stt_engine.py
Offline STT using faster-whisper.
Falls back to Google STT if Whisper not available.
"""

import logging
import speech_recognition as sr
import config

log = logging.getLogger("Manu.STT")


class STTEngine:
    def __init__(self):
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold        = getattr(config, "ENERGY_THRESHOLD", 300)
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold          = 0.8
        self._whisper = None
        self._load_whisper()

    def _load_whisper(self):
        try:
            from faster_whisper import WhisperModel
            model_size = getattr(config, "WHISPER_MODEL", "base")
            self._whisper = WhisperModel(model_size, device="cpu", compute_type="int8")
            log.info(f"STT: faster-whisper '{model_size}' loaded (offline)")
        except ImportError:
            log.warning("faster-whisper not found. Using Google STT (needs internet).")

    def calibrate_microphone(self, duration=1.5):
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)
            log.info(f"Mic calibrated. Threshold: {self._recognizer.energy_threshold:.0f}")
        except Exception as e:
            log.warning(f"Mic calibration failed: {e}")

    def listen(self, timeout=8, phrase_limit=15):
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            return self._transcribe(audio)
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            log.error(f"STT listen error: {e}")
            return None

    def _transcribe(self, audio):
        if self._whisper:
            return self._whisper_transcribe(audio)
        return self._google_transcribe(audio)

    def _whisper_transcribe(self, audio):
        import io, soundfile as sf
        try:
            wav = audio.get_wav_data(convert_rate=16000, convert_width=2)
            samples, _ = sf.read(io.BytesIO(wav), dtype="float32")
            segs, _ = self._whisper.transcribe(
                samples, language="en", beam_size=5, vad_filter=True
            )
            text = " ".join(s.text for s in segs).strip()
            log.info(f"Whisper: '{text}'")
            return text or None
        except Exception as e:
            log.error(f"Whisper transcribe error: {e}")
            return self._google_transcribe(audio)

    def _google_transcribe(self, audio):
        try:
            text = self._recognizer.recognize_google(audio, language="en-IN")
            log.info(f"Google STT: '{text}'")
            return text
        except Exception:
            return None
