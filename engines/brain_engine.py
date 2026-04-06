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
        """Update the active Ollama model (Task 7d)."""
        self.current_model = model_name
        return f"Model switched to {model_name}. I'm now using {model_name} for processing."

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
        """Generator for streaming Ollama responses (Task 7b)."""
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
        """Construct the Ollama chat payload with dynamic context (Task 7a, 7c)."""
        user_name = self.memory.get_setting("user_name", config.USER_NAME)
        now = datetime.datetime.now()
        date_str = now.strftime('%A %B %d, %Y at %H:%M')
        
        # 1. Personality & Habit Injection
        habit_summary = self.memory.get_top_habits(3)
        habit_str = ", ".join([h['pattern'] for h in habit_summary]) if habit_summary else "No patterns yet."
        
        # 2. Dynamic System Prompt (Task 7a)
        system_prompt = f"""
        You are Manu, a warm, witty local AI assistant.
        Current time: {date_str}
        User's name: {user_name}
        Current mood: {emotional_context}
        User's frequent habits: {habit_str}

        Personality rules:
        - Be concise (2-3 sentences unless asked for detail)
        - Use mild humor naturally, never forced
        - Reference past conversations when relevant
        - Vary response openers (never repeat the same opener twice in a row)
        - If unsure, ask a clarifying question rather than guessing
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 3. Contextual Recall (Task 3b)
        similars = self.memory.find_similar(text, limit=3)
        if similars:
            recall_text = " ".join([f"({m['timestamp']}) {m['role']}: {m['message']}" for m in similars])
            messages.append({"role": "system", "content": f"Recent relevant context: {recall_text}"})

        # 4. Rolling History (Task 7c)
        full_history = self.memory.build_llm_context(limit=25)
        if len(full_history) > 20:
            # Simple summarization placeholder for very long history
            summary_msg = {"role": "system", "content": "You have been talking to the user for a while now. Keep the momentum going."}
            messages.append(summary_msg)
            history = full_history[-8:] # Keep last 8 turns
        else:
            history = full_history[-8:] # Default 8-turn rolling window
            
        messages.extend(history)
        messages.append({"role": "user", "content": text})
        
        return {
            "model": self.current_model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": 0.7}
        }

    def _query_ollama(self, text, emotional_context=""):
        payload = self._build_payload(text, emotional_context, stream=False)
        try:
            r = requests.post(f"{self.ollama_host}/api/chat", json=payload, timeout=20)
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "").strip()
        except: pass
        return self._fallback_response(text)

    def _fallback_response(self, text):
        return "I'm currently unable to connect to my brain (Ollama). Please make sure the service is running."

    def is_available(self):
        return self.ollama_available
