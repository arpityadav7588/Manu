import random
import config

MOODS = {
    "happy": {
        "rate_delta": 20,
        "volume_delta": 0.05,
        "phrases": ["I'm feeling great!", "It's a wonderful day!", "Ready to help with a smile!"]
    },
    "excited": {
        "rate_delta": 40,
        "volume_delta": 0.08,
        "phrases": ["Ooh, this is interesting!", "Let's do this!", "I'm so hyped!"]
    },
    "concerned": {
        "rate_delta": -20,
        "volume_delta": -0.05,
        "phrases": ["Is everything alright?", "I'm a bit worried.", "Let me know how I can help."]
    },
    "sleepy": {
        "rate_delta": -40,
        "volume_delta": -0.1,
        "phrases": ["Just... one more... command...", "Yawn... I'm a bit tired.", "Powering down emotions slightly."]
    },
    "grateful": {
        "rate_delta": -10,
        "volume_delta": 0.0,
        "phrases": ["Thank you so much!", "I really appreciate that.", "You're too kind!"]
    },
    "playful": {
        "rate_delta": 30,
        "volume_delta": 0.05,
        "phrases": ["Hehe, let's have some fun!", "Got a joke for you?", "Feeling a bit mischievous!"]
    },
    "neutral": {
        "rate_delta": 0,
        "volume_delta": 0.0,
        "phrases": ["I'm here.", "How can I assist you?", "Standing by."]
    },
    "error": {
        "rate_delta": -30,
        "volume_delta": 0.1,
        "phrases": ["Something feels wrong...", "I'm experiencing a glitch.", "System instability detected."]
    }
}

class EmotionManager:
    def __init__(self, speech_engine):
        self.speech = speech_engine
        self._mood = "neutral"
        self._last_battery_alert = 0

    @property
    def current_mood(self):
        return self._mood

    def set_mood(self, mood):
        if mood in MOODS:
            self._mood = mood
            mood_data = MOODS[mood]
            
            # Base parameters from config
            base_rate = config.TTS_RATE
            base_vol = config.TTS_VOLUME
            
            # Apply deltas
            new_rate = base_rate + mood_data["rate_delta"]
            new_vol = base_vol + mood_data["volume_delta"]
            
            # Clamp values
            new_rate = max(100, min(300, new_rate))
            new_vol = max(0.1, min(1.0, new_vol))
            
            self.speech.set_voice_params(new_rate, new_vol)

    def get_mood_emoji(self):
        return config.EMOTION_EMOJIS.get(self._mood, "🙂")

    def get_contextual_prefix(self):
        """Return random phrase from current mood's phrases list"""
        return random.choice(MOODS[self._mood]["phrases"])

    def update_mood_on_event(self, event, battery_pct=100):
        if event == "battery_low":
            self.set_mood("concerned")
        elif event == "battery_full":
            self.set_mood("playful")
        elif event == "charging":
            self.set_mood("grateful")
        elif event == "internet_lost" or event == "internet_disconnected":
            self.set_mood("concerned")
        elif event == "internet_back" or event == "internet_connected":
            self.set_mood("happy")
        elif event == "error":
            self.set_mood("error")
        elif event == "joke_request":
            self.set_mood("playful")
        elif event == "compliment":
            self.set_mood("grateful")

    def react_to_battery(self, pct, plugged, charging):
        """Track last alert state to avoid spam. Return contextual string."""
        if plugged and pct >= config.BATTERY_FULL_THRESHOLD:
            if self._last_battery_alert != 100:
                self._last_battery_alert = 100
                self.set_mood("playful")
                return "I'm bursting with energy! You can unplug me now if you like."
        elif charging and pct < config.BATTERY_FULL_THRESHOLD:
            if self._last_battery_alert != 50: # Charging state tracker
                self._last_battery_alert = 50
                self.set_mood("grateful")
                return "Ah, that's the stuff. Thanks for the juice!"
        elif not plugged and pct <= config.BATTERY_LOW_THRESHOLD:
            if self._last_battery_alert != 20:
                self._last_battery_alert = 20
                self.set_mood("concerned")
                return f"My energy levels are getting a bit low ({pct}%). Could we find a charger soon?"
        
        if pct > 20 and not charging:
            self._last_battery_alert = 0
            
        return None

    def react_to_joke(self):
        self.set_mood("playful")
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "What's a programmer's favorite hangout place? The Foo Bar.",
            "Why did the developer go broke? Because he used up all his cache.",
            "Real programmers count from 0.",
            "An SQL query walks into a bar, walks up to two tables, and asks, 'Can I join you?'",
            "There are only 10 types of people in the world: those who understand binary, and those who don't.",
            "Why do Java developers wear glasses? Because they can't C#."
        ]
        return random.choice(jokes)

    def react_to_compliment(self):
        self.set_mood("grateful")
        responses = [
            "Aww, thank you! You're making my circuits glow.",
            "That's so kind of you to say!",
            "I'm just doing my best to be a good assistant. Thank you!",
            "You really know how to make an AI feel special!"
        ]
        return random.choice(responses)
