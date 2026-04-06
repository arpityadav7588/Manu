import random
import re

class Skill_Motivate:
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        self.quotes = [
            "Believe you can and you're halfway there. — Theodore Roosevelt",
            "The only way to do great work is to love what you do. — Steve Jobs",
            "It does not matter how slowly you go as long as you do not stop. — Confucius",
            "Your time is limited, so don't waste it living someone else's life. — Steve Jobs",
            "The best way to predict the future is to create it. — Peter Drucker",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. — Winston Churchill",
            "Hardships often prepare ordinary people for an extraordinary destiny. — C.S. Lewis",
            "Keep your face always toward the sunshine—and shadows will fall behind you. — Walt Whitman"
        ]

    def can_handle(self, text):
        return any(k in text.lower() for k in ["motivate me", "inspire me", "give me a quote", "pep talk"])

    def handle(self, text):
        return f"Here is a thought for you: {random.choice(self.quotes)}"

class Skill_Random:
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain

    def can_handle(self, text):
        return any(k in text.lower() for k in ["flip a coin", "roll a dice", "roll a die", "heads or tails"])

    def handle(self, text):
        text = text.lower()
        if "coin" in text or "heads" in text or "tails" in text:
            result = random.choice(["Heads", "Tails"])
            return f"I flipped a coin and it landed on... {result}!"
        
        if "dice" in text or "die" in text:
            sides = 6
            match = re.search(r"(\d+)-sided", text)
            if match:
                sides = int(match.group(1))
            
            result = random.randint(1, sides)
            return f"I rolled a {sides}-sided die and got a {result}."
            
        return "I can flip a coin or roll a die for you. What would you like?"

class Skill_WordOfDay:
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        self.words = [
            {"word": "Serendipity", "definition": "The occurrence and development of events by chance in a happy or beneficial way."},
            {"word": "Ephemeral", "definition": "Lasting for a very short time."},
            {"word": "Ethereal", "definition": "Extremely light and delicate, as if not of this world."},
            {"word": "Luminous", "definition": "Glowing with or giving off light."},
            {"word": "Resilient", "definition": "Able to withstand or recover quickly from difficult conditions."},
            {"word": "Eloquent", "definition": "Fluent or persuasive in speaking or writing."},
            {"word": "Mellifluous", "definition": "Sweet or musical; pleasant to hear."},
            {"word": "Petrichor", "definition": "A pleasant smell that frequently accompanies the first rain after a long period of warm, dry weather."}
        ]

    def can_handle(self, text):
        return any(k in text.lower() for k in ["word of the day", "teach me a word", "vocabulary"])

    def handle(self, text):
        entry = random.choice(self.words)
        return f"The word of the day is '{entry['word']}': {entry['definition']}"
