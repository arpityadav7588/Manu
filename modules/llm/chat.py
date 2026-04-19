"""
modules/llm/chat.py
Bridge/Wrapper for BrainEngine to match Siri-mode LLMEngine interface.
"""
import logging
from engines.brain_engine import BrainEngine

log = logging.getLogger("Manu.LLMChat")


class LLMChat(BrainEngine):
    """
    Extends BrainEngine (no-arg __init__) with the extra interface
    that main.py expects via LLMEngine:
      - __init__(memory) → stores memory ref, delegates to BrainEngine()
      - chat(text, context) → BrainEngine.chat()
      - is_available property
      - summarize_session()
    """

    def __init__(self, memory=None):
        super().__init__()          # BrainEngine takes no args
        self.memory = memory
        # Try to load user name from memory
        if memory:
            try:
                name = memory.get_setting("user_name")
                if name:
                    self.set_user_name(name)
            except Exception:
                pass
        log.info("LLMChat (Bridge) initialized.")

    def chat(self, text: str, context: str = "") -> str:
        """Delegates to BrainEngine.chat()."""
        # If context is empty but we have memory, build it
        if not context and self.memory:
            try:
                context = self.memory.build_llm_context(6)
            except Exception:
                pass
        return super().chat(text, context)

    @property
    def is_available(self):
        return super().is_available

    def summarize_session(self, interactions=None):
        """
        Produce a short, personality-driven summary of recent interactions.
        Uses Ollama for context-aware summarization if available.
        """
        if not self.is_available:
            return "Systems were nominal. No significant events to report."
        
        text = "Summarize our recent interaction in 1 sentence using your JARVIS personality."
        # Use memory if no interactions provided
        context = ""
        if not interactions and self.memory:
            context = self.memory.build_llm_context(10)
        
        try:
            return self.chat(text, context)
        except Exception:
            return "A productive session, sir. Ready for the next task."
