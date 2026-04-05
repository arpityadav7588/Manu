import ollama
import json

class BrainEngine:
    def __init__(self, model="llama3.2"):
        self.model = model
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are 'Manu', a witty, warm, and highly capable local AI assistant. "
                    "Your personality is human-like, helpful, and slightly humorous. "
                    "You care about the user's wellbeing. If the battery is low, act concerned. "
                    "If the charger is plugged in, act grateful or energized. "
                    "Always keep responses concise but personable."
                )
            }
        ]

    def chat(self, prompt, context=None):
        """
        Sends a prompt to the local Ollama LLM and returns the response.
        """
        if context:
            self.history.append({"role": "system", "content": f"Context: {context}"})
            
        self.history.append({"role": "user", "content": prompt})
        
        try:
            response = ollama.chat(model=self.model, messages=self.history)
            reply = response['message']['content']
            
            # Store history
            self.history.append({"role": "assistant", "content": reply})
            
            # Keep history manageable (last 10 turns)
            if len(self.history) > 20:
                self.history = [self.history[0]] + self.history[-19:]
                
            return reply
        except Exception as e:
            return f"I'm having a little trouble thinking right now. Error: {str(e)}"

    def get_personality_response(self, event_type, details=""):
        """
        Generates a quick personality-driven response for system events.
        """
        prompts = {
            "battery_low": "My energy is fading... I might need a recharge soon. Can you help?",
            "battery_full": "I'm fully charged and ready for anything! Let's get to work.",
            "charging": "Ah, that's the stuff. Thank you for plugging me in!",
            "internet_lost": "I've lost my connection to the digital world. I'll stay here for you though.",
            "internet_back": "I'm back online! The web is at our fingertips again."
        }
        return prompts.get(event_type, "I'm here.")

if __name__ == "__main__":
    # Test simple interaction
    brain = BrainEngine()
    print(brain.chat("Hello Manu, how are you today?"))
