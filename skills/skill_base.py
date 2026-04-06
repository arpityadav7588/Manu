from abc import ABC, abstractmethod

class BaseSkill(ABC):
    """
    Abstract base class for all Manu skills.
    Skills should inherit from this and implement can_handle and handle.
    """
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        self.name = self.__class__.__name__.replace("Skill_", "")

    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """Return True if this skill can handle the given text."""
        pass

    @abstractmethod
    def handle(self, text: str) -> str:
        """Execute the skill and return a string response."""
        pass
