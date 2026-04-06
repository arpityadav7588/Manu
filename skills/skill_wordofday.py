import random
from skills.skill_base import BaseSkill

class Skill_WordOfDay(BaseSkill):
    def __init__(self, tts, memory, brain):
        super().__init__(tts, memory, brain)
        self.words = [
            ("Ephemeral", "Lasting for a very short time."),
            ("Serendipity", "The occurrence of events by chance in a happy or beneficial way."),
            ("Lethargic", "Affected by lethargy; sluggish and apathetic."),
            ("Eloquence", "Fluent or persuasive speaking or writing.")
        ]

    def can_handle(self, text: str) -> bool:
        return "word of the day" in text or "learn a new word" in text

    def handle(self, text: str) -> str:
        word, meaning = random.choice(self.words)
        return f"Today's word is {word}. It means: {meaning}"
