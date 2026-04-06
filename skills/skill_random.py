import random
import re

class Skill_Random:
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain

    def can_handle(self, text):
        keywords = ["flip a coin", "roll a dice", "roll a die", "toss a coin", "random number"]
        return any(k in text.lower() for k in keywords)

    def handle(self, text):
        t = text.lower()
        if "coin" in t or "flip" in t or "toss" in t:
            result = random.choice(["Heads", "Tails"])
            return f"It's {result}."
        elif "dice" in t or "die" in t:
            sides = 6
            # Check for range, e.g., "roll a 20 sided die"
            match = re.search(r"(\d+)-?sided", t)
            if match:
                sides = int(match.group(1))
            res = random.randint(1, sides)
            return f"The die shows {res}."
        elif "random number" in t:
            res = random.randint(1, 100)
            return f"Random number (1-100): {res}."
            
        return "I'm not sure what you want me to generate."
