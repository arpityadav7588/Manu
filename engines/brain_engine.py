import requests
import json
import datetime
import config

class BrainEngine:
    def __init__(self, memory):
        self.memory = memory
        self.host = config.OLLAMA_HOST
        self.model = getattr(config, "LLM_MODEL", "llama3.2")
        self.system_prompt = (
            "You are Manu, a warm, witty local AI assistant. "
            "Speak warmly and use mild humor appropriately. "
            "Keep your answers between 2-4 sentences. "
            "Your user's name is Arpit. Addressing him as Arpit is encouraged."
        )

    def is_ollama_available(self) -> bool:
        """Check if Ollama server is reachable (Upgrade 2)."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def chat(self, text, emotional_context=""):
        """Main chat entry point with memory injection (Upgrade 2)."""
        if not self.is_ollama_available():
            return self._fallback_response(text)

        # Build messages with history (last 6 entries)
        history = self.memory.build_llm_context(limit=6)
        
        messages = [{"role": "system", "content": self.system_prompt}]
        if emotional_context:
            messages.append({"role": "system", "content": f"Current mood/context: {emotional_context}"})
        
        messages.extend(history)
        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }

        try:
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=20)
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            print(f"[X] Brain Error: {e}")
        
        return self._fallback_response(text)

    def summarize_session(self, interactions: list) -> str:
        """Summarize a list of interactions (Upgrade 2)."""
        if not interactions: return "No active interactions to summarize."
        
        text_to_sum = "\n".join([f"{i['role']}: {i['message']}" for i in interactions])
        prompt = f"Summarize the following chat session concisely in 2 sentences:\n\n{text_to_sum}"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        
        try:
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=15)
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "").strip()
        except:
            pass
        return "Session complete. It was a productive talk!"

    def _fallback_response(self, text):
        """Rule-based fallback when Ollama is unreachable (Upgrade 2)."""
        text = text.lower()
        fallbacks = {
            "hello": "Hello Arpit! I'm running in restricted mode, but I'm here for you.",
            "hi": "Hi there, Arpit! My brain is a bit offline, but I can still hear you.",
            "time": f"The current time is {datetime.datetime.now().strftime('%H:%M')}.",
            "joke": "Why did the computer show up late to work? It had a hard drive!",
            "what can you do": "I can manage your schedule, take notes, and help with your system. Usually I'm smarter with Ollama!",
            "who made you": "I was created by Arpit and refined by Antigravity.",
            "thank you": "You're very welcome, Arpit!",
            "bye": "Goodbye! I'll be here when you need me.",
            "status": "Ollama is currently unreachable, so I'm using my local fallback logic."
        }
        
        for key in fallbacks:
            if key in text:
                return fallbacks[key]
        
        return "I'm currently disconnected from my main brain (Ollama). I can still handle basic system commands though!"
