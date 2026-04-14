"""
modules/emotional/state_manager.py
Bridge for EmotionManager to match EmotionalStateManager interface.
"""
import logging
from modules.emotion_manager import EmotionManager

log = logging.getLogger("Manu.StateManager")

class EmotionalStateManager(EmotionManager):
    def __init__(self, tts=None):
        super().__init__()
        self.tts = tts
        self.gui = None
        log.info("EmotionalStateManager (Bridge) initialized.")

    def set_mood(self, mood: str):
        """New method expected by main.py."""
        self.current_mood = mood
        if self.gui:
            self.gui.update_emotion(self.get_mood_emoji())
        log.debug(f"Mood set to: {mood}")
