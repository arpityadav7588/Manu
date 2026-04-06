import threading
import time
import queue
from typing import Callable, Optional
import numpy as np
import pyaudio
import pygame
import wave
import os
import config

try:
    import openwakeword
    from openwakeword.model import Model
    HAS_OWW = True
except ImportError:
    HAS_OWW = False

class WakeWordDetector:
    """Manages audio capture and wake-word spotting using openWakeWord."""
    def __init__(self):
        self.running = False
        self.callback = None
        self.model = None
        self.audio_queue = queue.Queue()
        self.chunk_size = 1280
        self.rate = 16000
        self.last_detection = 0
        self.cooldown = 1.5
        self.confidence_threshold = 0.6
        
        self.wake_sound_path = config.DATA_DIR / "sounds" / "wake.wav"
        self._ensure_wake_sound()

        if HAS_OWW:
            try:
                # Load models requested in config (or default)
                self.model = Model(wakeword_models=config.WAKE_WORDS)
                print(f"[*] WakeWord: Loaded models: {config.WAKE_WORDS}")
            except Exception as e:
                print(f"[!] WakeWord: Initialization error: {e}")

    def _ensure_wake_sound(self):
        """Create a simple beep if wake.wav doesn't exist."""
        if not self.wake_sound_path.exists():
            print("[*] WakeWord: Generating default wake chime...")
            self.wake_sound_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                sample_rate = 44100
                duration = 0.2
                frequency = 880 # A5
                t = np.linspace(0, duration, int(sample_rate * duration))
                data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
                
                with wave.open(str(self.wake_sound_path), 'w') as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(sample_rate)
                    f.writeframes(data.tobytes())
            except: pass

    def _play_chime(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.Sound(str(self.wake_sound_path)).play()
        except: pass

    def _listen_worker(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print("[*] WakeWord: Listening...")
            while self.running:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                if HAS_OWW and self.model:
                    audio_np = np.frombuffer(data, dtype=np.int16)
                    prediction = self.model.predict(audio_np)
                    
                    for mdl in prediction:
                        score = prediction[mdl]
                        if score > self.confidence_threshold:
                            now = time.time()
                            if (now - self.last_detection) > self.cooldown:
                                self.last_detection = now
                                self._play_chime()
                                print(f"[*] Wake word detected: {mdl} ({score:.2f})")
                                if self.callback:
                                    self.callback()
                                # Allow time for callback to finish speaking/processing
                                time.sleep(1)
                else:
                    time.sleep(0.1)
                
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[X] WakeWord: Mic failure: {e}")
        finally:
            p.terminate()

    def start(self, callback: Callable):
        self.callback = callback
        self.running = True
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def stop(self):
        self.running = False
