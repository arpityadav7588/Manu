import requests

class BrainEngine:
    def __init__(self):
        try:
            self.model = "gemma4"
            self.ollama_url = "http://localhost:11434/api/chat"
            self.conversation_history = []
            self.available = False
            self._check_ollama()
        except Exception as e:
            print(f"Brain init error: {e}")

    def _check_ollama(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                if any("gemma4" in name for name in models):
                    self.available = True
                    print("✅ Gemma4 ready")
                    return
            print("⚠ Ollama not running or gemma4 not pulled. Run: ollama pull gemma4")
        except requests.exceptions.ConnectionError:
            print("⚠ Ollama not running or gemma4 not pulled. Run: ollama pull gemma4")
        except Exception as e:
            print(f"⚠ Ollama check failed: {e}")

    def chat(self, user_message: str, context: str = "") -> str:
        try:
            if not self.available:
                return self._fallback(user_message)
                
            system_msg = {
                "role": "system",
                "content": f"""You are Manu, a warm, witty, locally-running AI assistant on the user's laptop. You speak naturally, use light humor, recall past context, and keep replies to 2-4 sentences. Never start with "Certainly!" or "Of course!". Current emotional context: {context}"""
            }
            
            self.conversation_history.append({"role": "user", "content": user_message})
            
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
                
            payload = {
                "model": "gemma4",
                "messages": [system_msg] + self.conversation_history,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 250}
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=20)
            if response.status_code == 200:
                content = response.json().get("message", {}).get("content", "")
                self.conversation_history.append({"role": "assistant", "content": content})
                return content
            else:
                return self._fallback(user_message)
        except Exception as e:
            return self._fallback(user_message)

    def get_personality_response(self, event: str) -> str | None:
        try:
            responses = {
                "battery_low": "Hey, battery's running low! Mind plugging me in?",
                "charging": "Charging now — thank you for taking care of me!",
                "battery_full": "Fully charged! I feel like a new assistant. Someone might want to unplug me before I start doing backflips.",
                "internet_on": "Back online! I can feel the internet again.",
                "internet_off": "Lost internet. I'll manage offline for now."
            }
            return responses.get(event)
        except Exception as e:
            return None

    def _fallback(self, text: str) -> str:
        try:
            return "My AI brain isn't responding right now. Make sure 'ollama serve' is running and you have run 'ollama pull gemma4'."
        except Exception as e:
            return "Fallback error."
