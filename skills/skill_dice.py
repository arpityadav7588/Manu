import random
from skills.skill_base import BaseSkill

class Skill_Dice(BaseSkill):
    """Rolls dice or flips a coin."""
    def __init__(self, tts, memory, brain):
        super().__init__(tts, memory, brain)

    @property
    def triggers(self) -> list[str]:
        return ["roll a die", "roll dice", "flip a coin", "heads or tails"]

    def handle(self, text: str) -> str:
        if "flip" in text or "coin" in text:
            res = random.choice(["Heads", "Tails"])
            return f"The coin landed on: {res}."
        else:
            res = random.randint(1, 6)
            return f"You rolled a: {res}."
