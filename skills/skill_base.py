from abc import ABC, abstractmethod

class BaseSkill(ABC):
    """
    Abstract base class for all Manu skills.
    To create a new skill, inherit from this class and place it in the skills/ directory.
    """
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        self.name = self.__class__.__name__.lower()

    @property
    @abstractmethod
    def triggers(self) -> list[str]:
        """List of phrases that trigger this skill."""
        return []

    def can_handle(self, text: str) -> bool:
        """Check if the input text matches any of the triggers."""
        text_lower = text.lower().strip()
        return any(trigger in text_lower for trigger in self.triggers)

    @abstractmethod
    def handle(self, text: str) -> str:
        """Process the command and return a response string."""
        pass
