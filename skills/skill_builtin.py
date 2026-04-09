import random
import re

class Skill_Motivate:
    """Task 10: Motivational quotes skill."""
    def __init__(self, tts, memory, llm):
        self.tts = tts
        self.quotes = [
            "Your limitation—it's only your imagination.",
            "Push yourself, because no one else is going to do it for you.",
            "Sometimes later becomes never. Do it now.",
            "Great things never come from comfort zones.",
            "Dream it. Wish it. Do it.",
            "Success doesn't just find you. You have to go out and get it.",
            "The harder you work for something, the greater you'll feel when you achieve it.",
            "Don't stop when you're tired. Stop when you're done."
        ]

    def can_handle(self, text: str) -> bool:
        return any(k in text.lower() for k in ["motivate me", "inspire me", "give me a quote"])

    def handle(self, text: str) -> str:
        return random.choice(self.quotes)

class Skill_Random:
    """Task 10: Coin flip and dice roll skill."""
    def __init__(self, tts, memory, llm):
        self.tts = tts

    def can_handle(self, text: str) -> bool:
        return any(k in text.lower() for k in ["flip a coin", "roll a dice", "roll a"])

    def handle(self, text: str) -> str:
        text = text.lower()
        if "flip a coin" in text:
            return f"The coin landed on: {random.choice(['Heads', 'Tails'])}."
        
        # Roll a [N]-sided die
        match = re.search(r"roll a (\d+)-sided die", text)
        if match:
            sides = int(match.group(1))
            return f"You rolled a {sides}-sided die and got: {random.randint(1, sides)}."
        
        # Default 6-sided die
        return f"You rolled a dice and got: {random.randint(1, 6)}."

class Skill_WordOfDay:
    """Task 10: Word of the day skill."""
    def __init__(self, tts, memory, llm):
        self.tts = tts
        self.words = [
            ("Serendipity", "The occurrence and development of events by chance in a happy or beneficial way."),
            ("Ethereal", "Extremely delicate and light in a way that seems too perfect for this world."),
            ("Melancholy", "A feeling of pensive sadness, typically with no obvious cause."),
            ("Euphoria", "A feeling or state of intense excitement and happiness."),
            ("Luminous", "Full of or shedding light; bright or shining, especially in the dark."),
            ("Eloquent", "Fluent or persuasive in speaking or writing."),
            ("Defiance", "Open resistance; bold disobedience."),
            ("Resilience", "The capacity to recover quickly from difficulties; toughness.")
        ]

    def can_handle(self, text: str) -> bool:
        return any(k in text.lower() for k in ["word of the day", "teach me a word"])

    def handle(self, text: str) -> str:
        word, definition = random.choice(self.words)
        return f"Today's word is {word}: {definition}"
