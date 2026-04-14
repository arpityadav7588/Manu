"""
modules/commands/dispatcher.py
Bridge for CommandEngine to match CommandDispatcher interface.
"""
import logging
from engines.command_engine import CommandEngine

log = logging.getLogger("Manu.Dispatcher")

class CommandDispatcher(CommandEngine):
    def __init__(self, tts=None, memory=None, llm=None, emotional=None):
        # Map new names to existing ones
        super().__init__(brain=llm, speech=tts, memory=memory)
        self.emotional = emotional
        log.info("CommandDispatcher (Bridge) initialized.")

    def process(self, text: str) -> str | None:
        """New method name expected by main.py."""
        # 1. Try commands first
        response = self.execute_command(text)
        
        # 2. If no command response, fall back to LLM if brain exists
        if not response and self.brain:
            mood = "neutral"
            if self.emotional:
                mood = getattr(self.emotional, "current_mood", "neutral")
            response = self.brain.chat(text, mood)
            
        return response
