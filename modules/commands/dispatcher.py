"""
modules/commands/dispatcher.py
Bridge for CommandEngine to match CommandDispatcher interface.
Wires CommandEngine + LLM fallback together.
"""
import logging
from engines.command_engine import CommandEngine

log = logging.getLogger("Manu.Dispatcher")


class CommandDispatcher:
    """
    Wraps CommandEngine with LLM fallback.
    main.py instantiates this as:
        CommandDispatcher(tts=tts, memory=memory, llm=llm, emotional=emotional)
    and calls dispatcher.process(text).
    """

    def __init__(self, tts=None, memory=None, llm=None, emotional=None):
        self._command_engine = CommandEngine()
        self.tts       = tts
        self.memory    = memory
        self.llm       = llm        # LLMEngine / BrainEngine
        self.emotional = emotional
        log.info("CommandDispatcher initialized.")

    def process(self, text: str) -> str | None:
        """
        Main entry point called by main.py and SiriMode.
        1. Try command engine first
        2. If no match → fall to LLM
        """
        if not text or not text.strip():
            return None

        # 1. Try pattern-matched commands
        response = self._command_engine.execute_command(text)

        # 2. If command engine returned None → ask LLM
        if response is None and self.llm:
            context = ""
            if self.memory:
                try:
                    context = self.memory.build_llm_context(6)
                except Exception:
                    pass
            try:
                response = self.llm.chat(text, context)
            except Exception as e:
                log.error(f"LLM chat error: {e}")
                response = "I'm having trouble thinking right now. Try a direct command."

        # 3. Log interaction
        if response and self.memory:
            try:
                self.memory.log_interaction(text, response)
            except Exception:
                pass

        return response

    def execute_command(self, text: str) -> str | None:
        """Direct access to command engine (for backward compat)."""
        return self._command_engine.execute_command(text)
