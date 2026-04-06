import pyperclip
import threading
import time
import logging

class ClipboardAI:
    """Watches clipboard and provides AI-powered analysis on demand."""
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self._last_content = ""
        self._watching = False
        self.log = logging.getLogger("Manu.ClipboardAI")

    def get_and_process(self, instruction: str = "summarize") -> str:
        """Read clipboard content and process it with LLM."""
        try:
            content = pyperclip.paste().strip()
        except:
            return "I couldn't read your clipboard."

        if not content:
            return "Your clipboard is empty."

        if len(content) > 3000:
            content = content[:3000] + "..."

        prompt = f"{instruction.capitalize()} this text:\n\n{content}"
        self.log.info(f"ClipboardAI: {instruction} on {len(content)} chars")

        response = self.llm.chat(prompt)
        return response if response else "I couldn't process that clipboard content."
