import random

class Skill_Motivate:
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        self.quotes = [
            "Believe you can and you're halfway there.",
            "It does not matter how slowly you go as long as you do not stop.",
            "Everything you've ever wanted is on the other side of fear.",
            "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "Hardships often prepare ordinary people for an extraordinary destiny.",
            "Believe in yourself. You are braver than you think, more talented than you know, and capable of more than you imagine.",
            "Your limitation—it's only your imagination.",
            "Dream it. Wish it. Do it."
        ]

    def can_handle(self, text):
        keywords = ["motivate me", "inspire me", "give me a quote", "motivation"]
        return any(k in text.lower() for k in keywords)

    def handle(self, text):
        return f"Here's a thought for you: {random.choice(self.quotes)}"
