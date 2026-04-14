"""
engines/llm_engine.py
Thin wrapper — re-exports LLMChat from modules as LLMEngine.
"""

try:
    from modules.llm.chat import LLMChat as LLMEngine
except ImportError:
    # Fallback stub if modules/llm/chat.py doesn't exist yet
    class LLMEngine:
        def __init__(self, memory):
            self.memory = memory
        def chat(self, text, context=""): 
            return "LLM not configured. Start Ollama and set LLM_MODEL in config.py."
        def summarize_session(self, interactions): 
            return ""
        @property
        def is_available(self): 
            return False
