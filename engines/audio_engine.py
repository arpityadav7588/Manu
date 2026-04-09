import speech_recognition as sr
import io
import soundfile as sf
import numpy as np

class AudioEngine:
    def __init__(self, model="base"):
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.whisper_model = None
            self.whisper_available = False
            self._load_whisper(model)
        except Exception as e:
            print(f"Error init AudioEngine: {e}")

    def _load_whisper(self, model_size):
        try:
            from faster_whisper import WhisperModel
            self.whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.whisper_available = True
            print(f"✅ Whisper {model_size} loaded")
        except ImportError:
            self.whisper_available = False
            print("⚠ faster_whisper not available, using Google recognition fallback.")
        except Exception as e:
            self.whisper_available = False
            print(f"⚠ Whisper failed to load: {e}")

    def listen_and_recognize(self, timeout=8, phrase_limit=12) -> str:
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                
            if self.whisper_available:
                return self._whisper_transcribe(audio)
            else:
                return self.recognizer.recognize_google(audio).strip().lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"Listen error: {e}")
            return ""

    def _whisper_transcribe(self, audio) -> str:
        try:
            wav_data = audio.get_wav_data(convert_rate=16000, convert_width=2)
            wav_io = io.BytesIO(wav_data)
            data, samplerate = sf.read(wav_io, dtype="float32")
            if len(data.shape) > 1:
                data = data.mean(axis=1) # to mono
                
            segments, _ = self.whisper_model.transcribe(data, language="en", beam_size=3, vad_filter=True)
            text = " ".join([segment.text for segment in segments])
            return text.strip().lower()
        except Exception as e:
            print(f"Whisper transcribe error: {e}")
            return ""

    def calibrate(self, duration=1.5):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                print(f"Energy threshold calibrated to: {self.recognizer.energy_threshold}")
        except Exception as e:
            print(f"Calibrate error: {e}")
