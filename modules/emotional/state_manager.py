"""
modules/emotional/state_manager.py
Bridge for EmotionManager to match EmotionalStateManager interface.
"""
import logging
from modules.emotion_manager import EmotionManager

log = logging.getLogger("Manu.StateManager")


class EmotionalStateManager(EmotionManager):
    """
    Extends EmotionManager (no-arg __init__) with TTS + GUI integration.
    main.py instantiates as: EmotionalStateManager(tts)
    """

    def __init__(self, tts=None):
        super().__init__()          # EmotionManager takes no args
        self.tts = tts
        self.gui = None
        log.info("EmotionalStateManager (Bridge) initialized.")

    def set_mood(self, mood: str):
        """Set mood and optionally update GUI emoji."""
        super().set_mood(mood)
        if self.gui:
            try:
                self.gui.update_emotion(self.get_mood_emoji())
            except Exception:
                pass
        # Modulate TTS voice for current mood
        if self.tts:
            try:
                params = self.get_tts_params()
                self.tts.set_voice_params(
                    rate=params.get("rate"),
                    volume=params.get("volume")
                )
            except Exception:
                pass
        log.debug(f"Mood set to: {mood}")

    def update_mood_on_event(self, event: str, battery_pct: int = 100):
        """Override to also propagate to TTS/GUI."""
        new_mood = super().update_mood_on_event(event, battery_pct)
        self.set_mood(new_mood)
        return new_mood
