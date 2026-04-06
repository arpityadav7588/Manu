import random
from skills.skill_base import BaseSkill

class Skill_Dice(BaseSkill):
    def can_handle(self, text: str) -> bool:
        return "roll" in text and "dice" in text

    def handle(self, text: str) -> str:
        sides = 6
        if "d20" in text: sides = 20
        res = random.randint(1, sides)
        return f"Rolling a d{sides}... You got a {res}!"
