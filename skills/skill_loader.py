import os
import importlib.util
import inspect
from pathlib import Path
from skills.skill_base import BaseSkill

def load_skills(tts, memory, brain):
    """Scan skills/ directory and instantiate classes inheriting from BaseSkill."""
    skills_dir = Path(__file__).parent.resolve()
    skills_dict = {}
    
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
                    instance = obj(tts, memory, brain)
                    skills_dict[instance.name.lower()] = instance
            print(f"[*] Loaded skill module: {module_name}")
        except Exception as e:
            print(f"[X] Error loading {file.name}: {e}")
            
    return skills_dict

def try_skills(skills_dict, text):
    """Iterate through loaded skills to see if any can handle the command."""
    text_lower = text.lower().strip()
    for name, skill in skills_dict.items():
        if hasattr(skill, "can_handle") and skill.can_handle(text_lower):
            try:
                return skill.handle(text_lower)
            except Exception as e:
                print(f"⚠️ Error handling skill {name}: {e}")
                
    return None
