from skills.skill_base import BaseSkill

class Skill_WordOfDay(BaseSkill):
    """Provides a daily word with its definition."""
    def __init__(self, tts, memory, brain):
        super().__init__(tts, memory, brain)
        self.words = [
            ("Serendipity", "The occurrence and development of events by chance in a happy or beneficial way."),
            ("Ethereal", "Extremely delicate and light in a way that seems too perfect for this world."),
            ("Melancholy", "A feeling of pensive sadness, typically with no obvious cause."),
            ("Euphoria", "A feeling or state of intense excitement and happiness."),
            ("Luminous", "Full of or shedding light; bright or shining, especially in the dark.")
        ]

    @property
    def triggers(self) -> list[str]:
        return ["word of the day", "tell me a new word", "vocabulary"]

    def handle(self, text: str) -> str:
        import random
        w, d = random.choice(self.words)
        return f"Today's word is {w}: {d}"
