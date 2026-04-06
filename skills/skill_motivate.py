import random
from skills.skill_base import BaseSkill

class Skill_Motivate(BaseSkill):
    def __init__(self, tts, memory, brain):
        super().__init__(tts, memory, brain)
        self.quotes = [
            "Your limitation—it's only your imagination.",
            "Push yourself, because no one else is going to do it for you.",
            "Sometimes later becomes never. Do it now.",
            "Great things never come from comfort zones."
        ]

    def can_handle(self, text: str) -> bool:
        return any(k in text for k in ["motivate", "inspiration", "quote"])

    def handle(self, text: str) -> str:
        return random.choice(self.quotes)
