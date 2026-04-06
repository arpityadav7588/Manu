import random
from skills.skill_base import BaseSkill

class Skill_Motivate(BaseSkill):
    """Provides random motivational quotes."""
    def __init__(self, tts, memory, brain):
        super().__init__(tts, memory, brain)
        self.quotes = [
            "Your limitation—it's only your imagination.",
            "Push yourself, because no one else is going to do it for you.",
            "Sometimes later becomes never. Do it now.",
            "Great things never come from comfort zones.",
            "Dream it. Wish it. Do it.",
            "Success doesn't just find you. You have to go out and get it.",
            "The harder you work for something, the greater you'll feel when you achieve it.",
            "Don't stop when you're tired. Stop when you're done.",
            "Wake up with determination. Go to bed with satisfaction."
        ]

    @property
    def triggers(self) -> list[str]:
        return ["motivate me", "give me a quote", "inspire me", "motivational quote"]

    def handle(self, text: str) -> str:
        return f"Here is something for you: {random.choice(self.quotes)}"
