import pyttsx3

class SpeechEngine:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self._rate = 172
            self._volume = 0.93
            
            self.engine.setProperty('rate', self._rate)
            self.engine.setProperty('volume', self._volume)
            
            voices = self.engine.getProperty('voices')
            selected_voice = voices[0].id if voices else None
            for voice in voices:
                name_lower = voice.name.lower()
                if "david" in name_lower or "mark" in name_lower or "george" in name_lower:
                    selected_voice = voice.id
                    break
            if selected_voice:
                self.engine.setProperty('voice', selected_voice)
        except Exception as e:
            print(f"Error initializing speech engine: {e}")

    def speak(self, text: str):
        try:
            print(f"🔊 Manu: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except RuntimeError:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', self._rate)
                self.engine.setProperty('volume', self._volume)
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Failed to speak: {e}")
        except Exception as e:
            print(f"Error in speak: {e}")

    def set_rate(self, rate: int):
        try:
            self._rate = rate
            self.engine.setProperty('rate', self._rate)
        except Exception as e:
            pass

    def set_volume(self, volume: float):
        try:
            self._volume = volume
            self.engine.setProperty('volume', self._volume)
        except Exception as e:
            pass

    def set_emotion_params(self, mood: str):
        try:
            if mood == "excited":
                self.engine.setProperty('rate', self._rate + 20)
                self.engine.setProperty('volume', min(1.0, self._volume + 0.05))
            elif mood == "concerned":
                self.engine.setProperty('rate', max(50, self._rate - 15))
                self.engine.setProperty('volume', max(0.0, self._volume - 0.05))
            elif mood == "sleepy":
                self.engine.setProperty('rate', max(50, self._rate - 30))
                self.engine.setProperty('volume', max(0.0, self._volume - 0.1))
            elif mood == "happy":
                self.engine.setProperty('rate', self._rate + 8)
                self.engine.setProperty('volume', self._volume)
            elif mood == "neutral":
                self.engine.setProperty('rate', self._rate)
                self.engine.setProperty('volume', self._volume)
        except Exception as e:
            pass
