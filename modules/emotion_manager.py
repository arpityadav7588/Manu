"""
modules/emotion_manager.py
Phase 4 — Emotion manager with voice-linked modulation.
Maps system events AND face emotions to Manu's mood.
Drives voice prosody via speech_engine.apply_mood().
"""

import logging
import random

log = logging.getLogger("Manu.Emotion")

MOOD_CONFIG = {
    "enthusiastic": {
        "emoji": "🤩",
        "rate": 195, "volume": 0.95,
        "prefix": ["Excellent. ", "Outstanding. ", "Perfect. "],
        "description": "energized and enthusiastic",
    },
    "happy": {
        "emoji": "😊",
        "rate": 185, "volume": 0.92,
        "prefix": ["", "", "Right. "],
        "description": "upbeat and positive",
    },
    "neutral": {
        "emoji": "🙂",
        "rate": 175, "volume": 0.90,
        "prefix": ["", "", ""],
        "description": "calm and focused",
    },
    "playful": {
        "emoji": "😜",
        "rate": 190, "volume": 0.93,
        "prefix": ["Interesting. ", "", "Well then. "],
        "description": "in a playful mood",
    },
    "grateful": {
        "emoji": "🙏",
        "rate": 168, "volume": 0.88,
        "prefix": ["Appreciated. ", "Thank you for that. ", ""],
        "description": "appreciative and warm",
    },
    "concerned": {
        "emoji": "😟",
        "rate": 158, "volume": 0.82,
        "prefix": ["I should mention... ", "A note of concern: ", ""],
        "description": "a bit concerned",
    },
    "sleepy": {
        "emoji": "😴",
        "rate": 142, "volume": 0.75,
        "prefix": ["", ""],
        "description": "running low on energy",
    },
    "thinking": {
        "emoji": "🤔",
        "rate": 170, "volume": 0.88,
        "prefix": ["Let me think... ", ""],
        "description": "processing",
    },
}

# System event → mood mapping
EVENT_MOOD_MAP = {
    "battery_low":       "concerned",
    "charging":          "grateful",
    "battery_full":      "playful",
    "internet_lost":     "concerned",
    "internet_restored": "happy",
    "morning":           "enthusiastic",
    "evening":           "neutral",
    "error":             "concerned",
    "success":           "happy",
    "lock":              "sleepy",
}


class EmotionManager:

    def __init__(self):
        self.current_mood = "neutral"
        log.info("EmotionManager ready.")

    # ── Core Methods (unchanged signatures from Phase 1) ──────────────────────

    def update_mood_on_event(self, event: str, battery_pct: int = 100):
        """Map a system event to an appropriate mood. Called by SystemMonitor."""
        new_mood = EVENT_MOOD_MAP.get(event, "neutral")
        self.current_mood = new_mood
        log.debug(f"Mood → {new_mood} (event: {event})")
        return new_mood

    def set_mood(self, mood: str):
        """Directly set mood by name."""
        if mood in MOOD_CONFIG:
            self.current_mood = mood

    def get_mood_emoji(self) -> str:
        """Return emoji for current mood. Used by GUI status bar."""
        return MOOD_CONFIG.get(self.current_mood, MOOD_CONFIG["neutral"])["emoji"]

    def get_contextual_prefix(self) -> str:
        """Return a JARVIS-style prefix string for current mood."""
        prefixes = MOOD_CONFIG.get(
            self.current_mood, MOOD_CONFIG["neutral"]
        )["prefix"]
        return random.choice(prefixes)

    def get_tts_params(self) -> dict:
        """Return rate/volume dict for current mood. Used by speech engine."""
        cfg = MOOD_CONFIG.get(self.current_mood, MOOD_CONFIG["neutral"])
        return {"rate": cfg["rate"], "volume": cfg["volume"]}

    # ── Phase 3 Methods ───────────────────────────────────────────────────────

    def apply_to_speech(self, speech_engine):
        """Directly apply current mood to speech engine."""
        if speech_engine:
            speech_engine.apply_mood(self.current_mood)

    def get_mood_description(self) -> str:
        """Return human-readable description of current mood."""
        cfg = MOOD_CONFIG.get(self.current_mood, MOOD_CONFIG["neutral"])
        return cfg.get("description", "operational")

    def transition_mood(self, new_mood: str, speech_engine=None):
        """
        Change mood and apply voice modulation.
        Call this instead of set_mood() when you want voice to change.
        """
        old = self.current_mood
        self.set_mood(new_mood)
        log.info(f"Mood: {old} → {new_mood}")
        if speech_engine:
            self.apply_to_speech(speech_engine)

    # ── Phase 4 Methods ───────────────────────────────────────────────────────

    def update_from_face_emotion(
        self,
        face_emotion: str,
        speech_engine=None
    ) -> bool:
        """
        Update Manu's mood based on detected facial emotion.
        Returns True if mood changed, False if same as before.
        Called by VisionEngine when emotion is detected.
        """
        from engines.vision_engine import FACE_TO_MOOD
        mood, _comment = FACE_TO_MOOD.get(face_emotion, ("neutral", None))

        if mood == self.current_mood:
            return False

        self.transition_mood(mood, speech_engine)
        log.info(f"Mood updated from face emotion: {face_emotion} → {mood}")
        return True

    def get_vision_response(self, face_emotion: str) -> str | None:
        """
        Return a natural proactive comment about detected face emotion.
        Returns None for neutral/no-comment emotions.
        """
        responses = {
            "happy":    [
                "You seem to be in a good mood. Let's keep that going.",
                "Glad to see you're happy. What are we working on?",
            ],
            "sad":      [
                "You look a bit down. Take your time — I'm here.",
                "Everything alright? You seem a bit low.",
            ],
            "angry":    [
                "You look frustrated. Want me to help with whatever's causing it?",
                "Take a breath. Tell me what's wrong and we'll sort it out.",
            ],
            "fear":     [
                "You look worried about something. What's going on?",
                "Is everything okay? You seem a bit anxious.",
            ],
            "surprise": [
                "Something caught you off guard there.",
                "That was unexpected for you, I take it.",
            ],
        }
        options = responses.get(face_emotion)
        if options:
            return random.choice(options)
        return None
