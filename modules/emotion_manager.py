import random
import config

MOOD_CONFIG = {
    "happy":       {"rate": 10,  "volume": 0.05, "emoji": "😊"},
    "excited":     {"rate": 30,  "volume": 0.10, "emoji": "🤩"},
    "concerned":   {"rate": -15, "volume": -0.05, "emoji": "😟"},
    "sleepy":      {"rate": -40, "volume": -0.20, "emoji": "😴"},
    "playful":     {"rate": 20,  "volume": 0.03, "emoji": "😜"},
    "neutral":     {"rate": 0,   "volume": 0.00, "emoji": "🙂"},
    "grateful":    {"rate": -5,  "volume": 0.05, "emoji": "🙏"},
    "error":       {"rate": 0,   "volume": 0.10, "emoji": "😵"},
    "thinking":    {"rate": -10, "volume": -0.05, "emoji": "🤔"},
    "listening":   {"rate": 0,   "volume": 0.00, "emoji": "👂"}
}

MOOD_PREFIXES = {
    "happy": ["Sure thing!", "Absolutely!", "Great news!", "Wonderful!", "Happy to help!"],
    "excited": ["Oh wow!", "This is amazing!", "I'm so pumped!", "Fantastic!", "Let's go!"],
    "concerned": ["Hmm...", "Let me check...", "That's interesting...", "Wait—", "I noticed something..."],
    "sleepy": ["*Yawns*...", "I'm a bit tired, but...", "Drowsing here...", "Slow and steady..."],
    "playful": ["Guess what!", "Hehe!", "Let's do this!", "You want to play?", "Fun times!"],
    "grateful": ["Aww, thank you!", "That's so kind of you!", "Refreshing!", "Grateful for you!"],
    "error": ["Oops...", "System alert—", "Something went wrong...", "Houston, we have a problem..."],
    "thinking": ["Let me see...", "Processing that...", "Thinking about it...", "Give me a moment..."],
    "listening": ["I'm listening...", "Go ahead!", "All ears!", "Standing by..."],
    "neutral": ["", "", ""]
}

class EmotionManager:
    def __init__(self):
        self._mood = "neutral"
        self._last_battery_pct = 100
        self._last_battery_plugged = True
        self._last_internet_state = True
        self._last_battery_alert_time = 0

    def set_mood(self, mood: str):
        """Set active mood (Upgrade 4)."""
        if mood in MOOD_CONFIG:
            self._mood = mood
        else:
            self._mood = "neutral"

    @property
    def current_mood(self):
        return self._mood

    def get_mood_emoji(self) -> str:
        """Return emoji for current mood (Upgrade 4)."""
        return MOOD_CONFIG.get(self._mood, MOOD_CONFIG["neutral"])["emoji"]

    def get_contextual_prefix(self) -> str:
        """Return random short phrase matching current mood (Upgrade 4)."""
        prefixes = MOOD_PREFIXES.get(self._mood, [""])
        return random.choice(prefixes)

    def get_tts_params(self, base_rate=175, base_volume=0.92):
        """Return (rate, volume) adjusted by mood (Upgrade 4)."""
        deltas = MOOD_CONFIG.get(self._mood, MOOD_CONFIG["neutral"])
        new_rate = max(100, min(280, base_rate + deltas["rate"]))
        new_volume = max(0.2, min(1.0, base_volume + deltas["volume"]))
        return int(new_rate), float(new_volume)

    def react_to_battery(self, pct, plugged, charging) -> str:
        """Task 4: Dynamic battery reactions."""
        # Avoid repeat notifications if state unchanged
        if (pct == self._last_battery_pct and plugged == self._last_battery_plugged):
            return None
        
        self._last_battery_pct = pct
        self._last_battery_plugged = plugged

        # if full+plugged: playful joke
        if pct >= 95 and plugged:
            self.set_mood("playful")
            return "I'm fully charged! I feel like I could run a marathon... or at least compute one!"
        
        # if charging: grateful/warm thank-you
        if charging:
            self.set_mood("grateful")
            return "Ah, that's better. Thanks for the electricity, I was getting a bit faint!"
            
        # if low+unplugged (<=20%): worried message
        if pct <= 20 and not plugged:
            self.set_mood("concerned")
            return f"Heads up! My battery is down to {pct}%. Could we find a power source?"

        return None

    def react_to_internet(self, connected: bool) -> str:
        """Task 4: Internet state reactions."""
        if connected == self._last_internet_state:
            return None
        self._last_internet_state = connected
        if connected:
            self.set_mood("happy")
            return "We're back online! The world feels so much bigger now."
        else:
            self.set_mood("concerned")
            return "I've lost connection to the internet. I'll still do my best locally!"

    def react_to_error(self, context: str) -> str:
        """Task 4: Error reactions."""
        self.set_mood("error")
        return f"I hit a snag while {context}. My apologies!"

    def react_to_joke_request(self) -> str:
        """Task 4: Set playful mood and return a random joke."""
        self.set_mood("playful")
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "What's a programmer's favorite hangout place? The Foo Bar.",
            "Real programmers count from 0.",
            "Algorithm: A word used by programmers when they don't want to explain what they did."
        ]
        return random.choice(jokes)

    def react_to_compliment(self) -> str:
        """Task 4: Set grateful mood."""
        self.set_mood("grateful")
        return "That's so kind of you! You're making me blush... if I had a face."
