"""
modules/emotion_manager.py
Manu's emotional state — maps system events to mood,
voice modulation parameters, and JARVIS-style prefixes.
"""

import logging
import random

log = logging.getLogger("Manu.Emotion")

MOOD_CONFIG = {
    "enthusiastic": {
        "emoji": "🤩", "rate": 195, "volume": 0.95,
        "prefix": ["Excellent. ", "Outstanding. ", "Perfect. "],
    },
    "happy": {
        "emoji": "😊", "rate": 185, "volume": 0.92,
        "prefix": ["", "", "Right. "],
    },
    "neutral": {
        "emoji": "🙂", "rate": 175, "volume": 0.90,
        "prefix": ["", "", ""],
    },
    "playful": {
        "emoji": "😜", "rate": 190, "volume": 0.93,
        "prefix": ["Interesting. ", "", "Well then. "],
    },
    "grateful": {
        "emoji": "🙏", "rate": 168, "volume": 0.88,
        "prefix": ["Appreciated. ", "Thank you for that. ", ""],
    },
    "concerned": {
        "emoji": "😟", "rate": 158, "volume": 0.82,
        "prefix": ["I should mention... ", "A note of concern: ", ""],
    },
    "sleepy": {
        "emoji": "😴", "rate": 142, "volume": 0.75,
        "prefix": ["", ""],
    },
}


class EmotionManager:

    def __init__(self):
        self.current_mood = "neutral"
        log.info("EmotionManager ready. Default mood: neutral")

    def update_mood_on_event(self, event: str, battery_pct: int = 100):
        """Map a system event to an appropriate mood."""
        event_mood_map = {
            "battery_low":        "concerned",
            "charging":           "grateful",
            "battery_full":       "playful",
            "internet_lost":      "concerned",
            "internet_restored":  "happy",
            "morning":            "enthusiastic",
            "evening":            "neutral",
            "error":              "concerned",
            "success":            "happy",
            "lock":               "sleepy",
        }
        new_mood = event_mood_map.get(event, "neutral")
        self.current_mood = new_mood
        log.debug(f"Mood → {new_mood} (event: {event})")
        return new_mood

    def set_mood(self, mood: str):
        if mood in MOOD_CONFIG:
            self.current_mood = mood

    def get_mood_emoji(self) -> str:
        return MOOD_CONFIG.get(self.current_mood, MOOD_CONFIG["neutral"])["emoji"]

    def get_contextual_prefix(self) -> str:
        prefixes = MOOD_CONFIG.get(
            self.current_mood, MOOD_CONFIG["neutral"]
        )["prefix"]
        return random.choice(prefixes)

    def get_tts_params(self) -> dict:
        cfg = MOOD_CONFIG.get(self.current_mood, MOOD_CONFIG["neutral"])
        return {"rate": cfg["rate"], "volume": cfg["volume"]}
