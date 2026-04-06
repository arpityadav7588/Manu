import random
import config

MOOD_CONFIG = {
    "happy":     {"rate_delta": 10,  "volume_delta": 0.05, "color": "#34d399", "emoji": ":)"},
    "excited":   {"rate_delta": 25,  "volume_delta": 0.08, "color": "#fb923c", "emoji": "!!!"},
    "concerned": {"rate_delta": -15, "volume_delta": -0.05, "color": "#f87171", "emoji": ":-("},
    "sleepy":    {"rate_delta": -30, "volume_delta": -0.10, "color": "#94a3b8", "emoji": "zzz"},
    "playful":   {"rate_delta": 15,  "volume_delta": 0.03, "color": "#fbbf24", "emoji": "P-)"},
    "thinking":  {"rate_delta": 0,   "volume_delta": 0.00, "color": "#818cf8", "emoji": "..."},
    "neutral":   {"rate_delta": 0,   "volume_delta": 0.00, "color": "#6c63ff", "emoji": ":-|"},
    "listening": {"rate_delta": 0,   "volume_delta": 0.00, "color": "#22d3ee", "emoji": "O_O"},
    "grateful":  {"rate_delta": -5,  "volume_delta": 0.02, "color": "#34d399", "emoji": "<3"}
}

class EmotionManager:
    def __init__(self, tts_engine=None):
        self._mood = "neutral"
        self._last_battery_alert = 0
        self.mood_config = MOOD_CONFIG
        print(f"[*] Emotion: Dynamics loaded ({len(self.mood_config)} moods).")

    @property
    def current_mood(self):
        return self._mood

    def set_mood(self, mood):
        if mood in MOOD_CONFIG:
            self._mood = mood
        else:
            self._mood = "neutral"

    def get_mood_emoji(self):
        return MOOD_CONFIG.get(self._mood, MOOD_CONFIG["neutral"])["emoji"]

    def get_hologram_color(self):
        """Return hex color for current mood for the 3D avatar."""
        return MOOD_CONFIG.get(self._mood, MOOD_CONFIG["neutral"])["color"]

    def apply_voice_modulation(self, tts_engine, base_rate=175, base_vol=0.92):
        """Apply rate and volume deltas to the TTS engine based on mood."""
        config = MOOD_CONFIG.get(self._mood, MOOD_CONFIG["neutral"])
        new_rate = base_rate + config["rate_delta"]
        new_vol = base_vol + config["volume_delta"]
        
        # Clamp values
        new_rate = max(100, min(250, new_rate))
        new_vol = max(0.2, min(1.0, new_vol))
        
        try:
            tts_engine.setProperty("rate", new_rate)
            tts_engine.setProperty("volume", new_vol)
        except Exception as e:
            print(f"⚠️ Voice modulation error: {e}")

    def update_mood_on_event(self, event, detail=None):
        if event == "battery_low":
            self.set_mood("concerned")
        elif event == "battery_full":
            self.set_mood("playful")
        elif event == "charging":
            self.set_mood("grateful")
        elif event == "internet_disconnected":
            self.set_mood("concerned")
        elif event == "internet_connected":
            self.set_mood("happy")
        elif event == "error":
            self.set_mood("concerned")

    def react_to_battery_event(self, percent, plugged):
        """Check battery status and return a personality-driven string."""
        if plugged and percent >= 95:
            self.set_mood("playful")
            return "I'm fully charged! Ready for some fun? Maybe a joke?"
        elif plugged and percent < 95:
            self.set_mood("grateful")
            return "Ah, that's refreshing. Thanks for the electricity!"
        elif not plugged and percent <= 20:
            self.set_mood("concerned")
            return f"I'm feeling a bit weak ({percent}%). Could we find a power source?"
        
        return None

    def react_to_joke(self):
        self.set_mood("playful")
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "What's a programmer's favorite hangout place? The Foo Bar.",
            "Real programmers count from 0."
        ]
        return random.choice(jokes)

    def react_to_compliment(self):
        self.set_mood("grateful")
        return "Aww, thank you! You're making my circuits glow."
