import speech_recognition as sr
import numpy as np
import soundfile as sf
import io
import threading
import config

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False

class AudioEngine:
    def __init__(self, model="base"):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = False
        self.model_name = model
        self.whisper_model = None
        
        if HAS_FASTER_WHISPER and config.STT_ENGINE == "whisper":
            try:
                # Use CPU for local compliance, can be changed to "cuda" if available
                self.whisper_model = WhisperModel(model, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"Error loading FasterWhisper: {e}")

    def listen_and_recognize(self, timeout=None, phrase_limit=None):
        """Open mic, capture audio, and transcribe."""
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                
                if config.STT_ENGINE == "whisper":
                    return self._transcribe_whisper(audio)
                else:
                    return self._transcribe_google(audio)
        except Exception as e:
            print(f"Audio capture error: {e}")
            return ""

    def _transcribe_whisper(self, audio):
        """Transcribe using Faster-Whisper or fallback."""
        try:
            # Convert sr.AudioData to float32 numpy array
            wav_data = io.BytesIO(audio.get_wav_data())
            audio_array, sample_rate = sf.read(wav_data)
            audio_array = audio_array.astype(np.float32)

            if self.whisper_model:
                segments, info = self.whisper_model.transcribe(audio_array, beam_size=5)
                text = " ".join([segment.text for segment in segments]).strip()
                return text
            else:
                # Fallback to Google if whisper fails to load
                return self._transcribe_google(audio)
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return self._transcribe_google(audio)

    def _transcribe_google(self, audio):
        """Standard Google Web Speech API fallback."""
        try:
            return self.recognizer.recognize_google(audio).strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Google STT Request Error: {e}")
            return ""

    def listen_for_command(self):
        """Short listener after wake word."""
        return self.listen_and_recognize(
            timeout=config.STT_LISTEN_TIMEOUT,
            phrase_limit=config.STT_PHRASE_LIMIT
        )

    def calibrate(self):
        """Adjust for ambient noise."""
        try:
            with sr.Microphone() as source:
                print("🤫 Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        except Exception as e:
            print(f"Calibration error: {e}")

    def detect_wake_word(self):
        """Listen in short bursts for wake words."""
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=4)
                text = self._transcribe_whisper(audio).lower()
                
                for word in config.WAKE_WORDS:
                    if word in text:
                        return True
                return False
        except Exception:
            return False
