import os
import importlib.util
import inspect
from pathlib import Path
from skills.skill_base import BaseSkill

class SkillLoader:
    """Scans and loads custom skills from the skills/ directory."""
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        self.skills = {}
        self.load_all()

    def load_all(self):
        """Scan skills/ directory and instantiate classes inheriting from BaseSkill."""
        skills_dir = Path(__file__).parent.parent / "skills"
        self.skills = {}
        
        for file in skills_dir.glob("skill_*.py"):
            if file.name in ["skill_loader.py", "skill_base.py"]:
                continue
                
            module_name = f"skills.{file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                        instance = obj(self.tts, self.memory, self.brain)
                        self.skills[instance.name.lower()] = instance
                print(f"[*] Loaded skill: {module_name}")
            except Exception as e:
                print(f"[X] Error loading skill {file.name}: {e}")

    def try_skills(self, text: str) -> str:
        """Iterate through loaded skills to see if any can handle the command."""
        text_lower = text.lower().strip()
        for name, skill in self.skills.items():
            if skill.can_handle(text_lower):
                try:
                    return skill.handle(text_lower)
                except Exception as e:
                    print(f"⚠️ Error handling skill {name}: {e}")
        return None
