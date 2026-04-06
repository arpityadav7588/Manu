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
        self.current_model = config.LLM_MODEL
        self.ollama_available = False
        self._check_ollama()

    def switch_model(self, model_name):
        """Update the active Ollama model."""
        self.current_model = model_name
        return f"Model switched to {model_name}"

    def _check_ollama(self):
        """Check if Ollama is reachable."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            self.ollama_available = (response.status_code == 200)
            if self.ollama_available:
                print("🧠 Brain Engine: Ollama is online.")
        except Exception:
            self.ollama_available = False

    def chat(self, text, emotional_context=""):
        """Query Ollama or fallback logic (Blocking)."""
        if self.ollama_available:
            return self._query_ollama(text, emotional_context)
        else:
            return self._fallback_response(text)

    def stream_chat(self, text, emotional_context=""):
        """Generator for streaming Ollama responses."""
        if not self.ollama_available:
            yield self._fallback_response(text)
            return

        payload = self._build_payload(text, emotional_context, stream=True)
        try:
            r = requests.post(f"{self.ollama_host}/api/chat", json=payload, stream=True, timeout=30)
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if not chunk.get("done"):
                        content = chunk.get("message", {}).get("content", "")
                        yield content
        except Exception as e:
            yield f"Error: {e}"

    def _build_payload(self, text, emotional_context="", stream=False):
        """Construct the Ollama chat payload with full context."""
        user_name = self.memory.get_setting("user_name", config.USER_NAME)
        date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Phase 1: Dynamic Personality injection
        personality = self.memory.build_personality_context()
        
        system_prompt = (
            f"You are Manu, a warm witty local AI assistant. {personality} "
            f"Keep replies to 2-3 sentences. Today: {date_str}. "
            f"User context: {emotional_context}"
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Phase 1: Contextual Recall (Task 3)
        similars = self.memory.find_similar(text, limit=2)
        if similars:
            recall_text = " ".join([m['message'] for m in similars])
            messages.append({"role": "system", "content": f"Relevant past context: {recall_text}"})

        # Add historical context (Task 7: 8-turn rolling)
        history = self.memory.build_llm_context(limit=8)
        messages.extend(history)
        
        messages.append({"role": "user", "content": text})
        
        return {
            "model": self.current_model,
            "messages": messages,
            "stream": stream
        }

    def _query_ollama(self, text, emotional_context=""):
        payload = self._build_payload(text, emotional_context, stream=False)
        
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
