import os
import importlib.util
from pathlib import Path

def load_skills(tts, memory, brain):
    """Scan skills/ directory for skill_*.py files and instantiate classes."""
    skills_dir = Path(__file__).parent.resolve()
    skills_dict = {}
    
    # Scan for skill_*.py files
    for file in skills_dir.glob("skill_*.py"):
        if file.name == "skill_loader.py":
            continue
            
        module_name = f"skills.{file.stem}"
        try:
            # Use importlib to load the module
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all classes that start with Skill_
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.startswith("Skill_") and obj.__module__ == module_name:
                    # Instantiate with required engines
                    instance = obj(tts, memory, brain)
                    skills_dict[name.lower()] = instance
            print(f"[*] Loaded skills from {module_name}")
        except Exception as e:
            print(f"[X] Failed to load skill from {file.name}: {e}")
            
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
