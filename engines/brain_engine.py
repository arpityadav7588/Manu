import requests
import json
import datetime
import config

SYSTEM_PROMPT = """
You are Manu, a warm, witty, and concise AI assistant. 
You provide helpful responses in 2-4 sentences max. 
Use humor appropriately when fitting. 
Never start your responses with 'Certainly!' or 'Of course!'. 
Always address the user as {user_name}. 
Today's date is {date}.
"""

class BrainEngine:
    def __init__(self, memory):
        self.memory = memory
        self.ollama_host = config.OLLAMA_HOST
        self.ollama_available = False
        self._check_ollama()

    def _check_ollama(self):
        """Check if Ollama is reachable."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            self.ollama_available = (response.status_code == 200)
            if self.ollama_available:
                print("🧠 Brain Engine: Ollama is online.")
        except Exception:
            self.ollama_available = False

    def chat(self, text, context=""):
        """Query Ollama or fallback logic."""
        if self.ollama_available:
            return self._query_ollama(text)
        else:
            return self._fallback_response(text)

    def _query_ollama(self, text):
        user_name = self.memory.get_setting("user_name", config.USER_NAME)
        date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        system_prompt = (
            f"You are Manu, a warm witty local AI assistant. Keep replies to 2-3 sentences. "
            f"Never start with 'Certainly!' or 'Of course!'. Today: {date_str}. User: {user_name}."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add historical context from SQLite
        history = self.memory.build_llm_context(limit=8)
        messages.extend(history)
        
        # Add current message
        messages.append({"role": "user", "content": text})
        
        payload = {
            "model": config.LLM_MODEL,
            "messages": messages,
            "stream": False
        }
        
        try:
            r = requests.post(f"{self.ollama_host}/api/chat", json=payload, timeout=20)
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            print(f"Ollama Error: {e}")
            
        return self._fallback_response(text)

    def _fallback_response(self, text):
        text = text.lower()
        if "hello" in text or "hi " in text: return "Hello! I'm here, though my brain (Ollama) is currently resting."
        if "who are you" in text: return "I am Manu, your personal assistant. Currently running in basic mode."
        return "I'm currently offline (no Ollama). How else can I help?"

    def is_available(self):
        return self.ollama_available
