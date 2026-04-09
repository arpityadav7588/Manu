import time
import random

class EmotionManager:
    def __init__(self):
        try:
            self.current_mood = "neutral"
            self._mood_time = time.time()
            
            self.MOOD_MAP = {
                "battery_low":  "concerned",
                "charging":     "grateful",
                "battery_full": "excited",
                "internet_on":  "happy",
                "internet_off": "concerned",
                "high_cpu":     "concerned",
                "error":        "error",
            }
            
            self.EMOJIS = {
                "happy":"😊", "excited":"🤩", "concerned":"😟", 
                "grateful":"🙏", "playful":"😜", "neutral":"🙂",
                "thinking":"🤔", "listening":"👂", "sleepy":"😴", "error":"😵"
            }
            
            self.PREFIXES = {
                "excited":   ["Oh wow! ", "This is exciting! "],
                "concerned":  ["Hmm... ", "I'm a little worried, but — "],
                "grateful":   ["Aww, thanks! ", "That's really kind. "],
                "happy":      ["Great! ", "Love it! "],
                "playful":    ["Ooh! ", "Ha! "],
                "neutral":    ["", "Sure. ", "Got it. "],
            }
        except Exception as e:
            pass

    def update_mood_on_event(self, event: str, battery_level: int = 100):
        try:
            if event in self.MOOD_MAP:
                self.current_mood = self.MOOD_MAP[event]
                self._mood_time = time.time()
        except Exception as e:
            pass

    def get_mood_emoji(self) -> str:
        try:
            return self.EMOJIS.get(self.current_mood, "🙂")
        except Exception as e:
            return "🙂"

    def get_contextual_prefix(self) -> str:
        try:
            prefixes = self.PREFIXES.get(self.current_mood, [""])
            return random.choice(prefixes)
        except Exception as e:
            return ""

    def auto_reset(self):
        try:
            if time.time() - self._mood_time > 300:
                self.current_mood = "neutral"
        except Exception as e:
            pass
