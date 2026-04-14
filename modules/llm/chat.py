"""
modules/llm/chat.py
Bridge/Wrapper for BrainEngine to match Siri-mode LLMChat interface.
"""
import logging
from engines.brain_engine import BrainEngine

log = logging.getLogger("Manu.LLMChat")

class LLMChat(BrainEngine):
    def __init__(self, memory=None):
        super().__init__(memory=memory)
        log.info("LLMChat (Bridge) initialized.")

    def chat(self, text: str, context: str = "") -> str:
        """Proposed main.py calls this directly."""
        return super().chat(text, context)

    @property
    def is_available(self):
        return self.available
        
    def summarize_session(self, interactions):
        return ""
