import os
import importlib.util
import inspect
from pathlib import Path

def load_skills(engines_dict):
    """Scan skills/ directory and load classes (Upgrade 10)."""
    skills_dir = Path(__file__).parent.resolve()
    loaded_skills = {}
    
    # Engines
    tts = engines_dict.get('tts')
    memory = engines_dict.get('memory')
    llm = engines_dict.get('brain')

    for file in skills_dir.glob("skill_*.py"):
        if file.name == "skill_loader.py": continue
        
        module_name = f"skills.{file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find classes starting with Skill_
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.startswith("Skill_"):
                instance = obj(tts=tts, memory=memory, llm=llm)
                loaded_skills[name.lower()] = instance
                print(f"[*] Skill Loaded: {name}")
                
    return loaded_skills
