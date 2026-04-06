import threading
import time
import queue
from typing import Callable, Optional
import numpy as np
import pyaudio
import pygame
pygame.mixer.init()

try:
    import openwakeword
    from openwakeword.model import Model
    HAS_OWW = True
except ImportError:
    HAS_OWW = False

import config

class WakeWordDetector:
    def __init__(self):
        global HAS_OWW
        self.running = False
        self.callback = None
        self.model = None
        self.audio_queue = queue.Queue()
        self.chunk_size = 1280
        self.rate = 16000
        self.last_detection = 0
        self.cooldown = 1.5 # Task 12: 1.5s cooldown
        self.confidence_threshold = 0.6 # Task 12: Confidence gating
        
        if HAS_OWW:
            try:
                # Let openwakeword find its default pretrained models
                self.model = Model()
                print("[*] WakeWord: openWakeWord initialized with default models.")
            except Exception as e:
                print(f"[!] WakeWord: Initialization error: {e}")
                HAS_OWW = False

    def _listen_worker(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.running:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                if HAS_OWW and self.model:
                    # Process with openWakeWord
                    audio_np = np.frombuffer(data, dtype=np.int16)
                    prediction = self.model.predict(audio_np)
                    
                    for mdl in prediction:
                        score = prediction[mdl]
                        if score > self.confidence_threshold:
                            now = time.time()
                            if (now - self.last_detection) > self.cooldown:
                                self.last_detection = now
                                self._play_beep()
                                print(f"[*] Wake word detected: {mdl} ({score:.2f})")
                                if self.callback:
                                    self.callback()
                else:
                    time.sleep(0.1)
                
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[X] WakeWord: Mic error: {e}")
        finally:
            p.terminate()

    def _play_beep(self):
        """Play a short detection beep using pygame or winsound."""
        try:
            # Try Windows beep as a robust fallback
            import winsound
            winsound.Beep(1000, 150)
        except:
            pass

    def start(self, callback: Callable):
        self.callback = callback
        self.running = True
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def stop(self):
        self.running = False

def fallback_check(text: str) -> bool:
    """Helper for Whisper-based spotting used in audio_engine."""
    keywords = ["manu", "star"]
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)
