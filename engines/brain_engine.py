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
        self.conversation = []
        self._check_ollama()

    def _check_ollama(self):
        """Check if Ollama is reachable."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            if response.status_code == 200:
                self.ollama_available = True
                print("🧠 Brain Engine: Ollama is available.")
            else:
                self.ollama_available = False
        except Exception:
            self.ollama_available = False
            print("⚠️ Brain Engine: Ollama not found. Using fallback logic.")

    def chat(self, text, context=""):
        """Append to session conversation and query LLM."""
        self.conversation.append({"role": "user", "content": text})
        
        response = ""
        if self.ollama_available:
            response = self._query_ollama(text)
        else:
            response = self._fallback_response(text)

        if response:
            self.conversation.append({"role": "assistant", "content": response})
            # Trim conversation to config limit
            if len(self.conversation) > config.LLM_CONTEXT_MSGS * 2:
                self.conversation = self.conversation[-(config.LLM_CONTEXT_MSGS * 2):]
            
        return response

    def _query_ollama(self, text):
        """POST to /api/chat."""
        url = f"{self.ollama_host}/api/chat"
        payload = {
            "model": config.LLM_MODEL,
            "messages": self._build_messages(),
            "stream": False,
            "options": {
                "temperature": config.LLM_TEMPERATURE,
                "num_predict": config.LLM_MAX_TOKENS
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "").strip()
            else:
                return f"Error from Ollama: {response.text}"
        except Exception as e:
            print(f"Ollama Query Error: {e}")
            return self._fallback_response(text)

    def _build_messages(self):
        """Build message list for LLM context."""
        user_name = self.memory.get_setting("user_name", config.USER_NAME)
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        
        system_msg = {
            "role": "system", 
            "content": SYSTEM_PROMPT.format(user_name=user_name, date=date_str)
        }
        
        memory_context = self.memory.build_llm_context(config.MEMORY_CONTEXT_LIMIT)
        
        return [system_msg] + memory_context + self.conversation

    def get_personality_response(self, event):
        """Proactive strings for system events."""
        user_name = self.memory.get_setting("user_name", config.USER_NAME)
        responses = {
            "battery_low": f"Hey {user_name}, I'm feeling a bit faint. Could we find a power source soon?",
            "battery_full": "I'm fully charged and ready to conquer the world! Or at least your desktop.",
            "charging": "Ah, that's refreshing! Thanks for the electricity, {user_name}.",
            "internet_connected": "I'm back online! The digital world feels so much closer now.",
            "internet_disconnected": f"It seems we've lost our connection, {user_name}. I'll stay here and keep you company offline."
        }
        return responses.get(event)

    def _fallback_response(self, text):
        """Rule-based replies for when Ollama is offline."""
        text = text.lower()
        if "how are you" in text:
            return "I'm performing optimally, though I'd be even better if my brain engine (Ollama) was online!"
        if "what can you do" in text:
            return "I can help with system tasks, take notes, set reminders, and chat — though my chat is a bit basic without Ollama."
        if "who made you" in text:
            return "I was created by a talented individual as your local assistant."
        if "thank you" in text or "thanks" in text:
            return "You're very welcome! I'm here to help."
        if "goodbye" in text or "bye" in text:
            return "Goodbye! See you next time."
            
        return "I'm currently in basic mode. Please start Ollama to enable my full conversational brain!"

    def summarize_session(self, interactions):
        """POST to Ollama asking it to summarize."""
        if not self.ollama_available or not interactions:
            return "No session summary available."
            
        url = f"{self.ollama_host}/api/chat"
        prompt = f"Summarize our latest interaction in 2-3 concise sentences: {json.dumps(interactions)}"
        payload = {
            "model": config.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "").strip()
        except Exception:
            pass
        return "The session has concluded successfully."

    @property
    def is_available(self):
        return self.ollama_available
