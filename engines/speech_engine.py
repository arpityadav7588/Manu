import pyttsx3
import threading
import config

class SpeechEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.lock = threading.Lock()
        
        # Auto-select a male English voice
        voices = self.engine.getProperty('voices')
        selected_voice = None
        for voice in voices:
            name = voice.name.lower()
            if "english" in name or "en-us" in name or "en-gb" in name:
                if any(m in name for m in ["david", "mark", "george", "male", "zira" if "male" not in name else ""]):
                    selected_voice = voice.id
                    break
        
        if selected_voice:
            self.engine.setProperty('voice', selected_voice)
        
        # Set rate and volume from config
        self.engine.setProperty('rate', config.TTS_RATE)
        self.engine.setProperty('volume', config.TTS_VOLUME)

    def speak(self, text):
        """Speak text synchronously with a lock to prevent concurrent calls."""
        with self.lock:
            print(f"🔊 Manu: {text}")
            self.engine.say(text)
            self.engine.runAndWait()

    def speak_async(self, text):
        """Speak in a daemon background thread."""
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()

    def set_rate(self, rate):
        """Set voice rate."""
        self.engine.setProperty('rate', rate)

    def set_volume(self, vol):
        """Set voice volume."""
        self.engine.setProperty('volume', vol)

    def set_voice_params(self, rate, volume):
        """Update both rate and volume properties live."""
        self.set_rate(rate)
        self.set_volume(volume)
