import random

class EmotionManager:
    def __init__(self):
        self.moods = ["cheerful", "witty", "concerned", "low_energy", "protective"]
        self.current_mood = "cheerful"
        
    def get_mood_emoji(self):
        mood_to_emoji = {
            "cheerful": "😊",
            "witty": "😏",
            "concerned": "😟",
            "low_energy": "🔋",
            "protective": "🛡️"
        }
        return mood_to_emoji.get(self.current_mood, "😐")

    def update_mood_on_event(self, event, battery_level=100):
        if event == "battery_low":
            self.current_mood = "low_energy"
        elif event == "charging":
            self.current_mood = "cheerful"
        elif event == "internet_lost":
            self.current_mood = "concerned"
        elif event == "security_lock":
            self.current_mood = "protective"
        elif event == "unplugged":
            if battery_level < 30:
                self.current_mood = "concerned"
            else:
                self.current_mood = "witty"

    def get_contextual_prefix(self):
        prefixes = {
            "cheerful": ["I'm feeling great! ", "Happy to help. ", "Look at us, getting things done! "],
            "witty": ["Well, since you asked so nicely... ", "I've got the answers, you've got the questions. ", "My circuits are buzzing with ideas. "],
            "concerned": ["I'm a bit worried about our status, but ", "Let's be quick, things seem unstable. ", "I'm monitoring everything closely. "],
            "low_energy": ["I'm feeling a bit drained... ", "I'll try my best with the energy I have left. ", "Maybe we should take a break? "],
            "protective": ["Your data is safe with me. ", "I'm standing guard. ", "Access restricted to authorized personnel only. "]
        }
        return random.choice(prefixes.get(self.current_mood, [""]))

if __name__ == "__main__":
    emotions = EmotionManager()
    emotions.update_mood_on_event("battery_low")
    print(emotions.get_mood_emoji(), emotions.get_contextual_prefix())
