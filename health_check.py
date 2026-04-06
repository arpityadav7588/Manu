import os
import sys
import socket
import importlib.util
import requests
import pyaudio
import cv2
import config

# Color constants for Windows/Console
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

TICK = f"{GREEN}[V]{RESET}"
WARN = f"{YELLOW}[!]{RESET}"
CROSS = f"{RED}[X]{RESET}"

def check_module(name):
    """Check if a module is installed."""
    if importlib.util.find_spec(name) is not None:
        return f"{TICK} {name}"
    else:
        return f"{CROSS} {name} (Missing)"

def check_ollama():
    """Check if Ollama server is reachable."""
    try:
        resp = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=2)
        if resp.status_code == 200:
            return f"{TICK} Ollama Server: Online ({config.LLM_MODEL})"
    except:
        pass
    return f"{CROSS} Ollama Server: Offline"

def check_mic():
    """Check if a microphone is accessible."""
    try:
        p = pyaudio.PyAudio()
        info = p.get_default_input_device_info()
        count = p.get_device_count()
        p.terminate()
        return f"{TICK} Microphone: {info['name']} ({count} devices found)"
    except:
        return f"{CROSS} Microphone: Not accessible"

def check_camera():
    """Check if a webcam is accessible."""
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret: return f"{TICK} Webcam: Online"
    except:
        pass
    return f"{CROSS} Webcam: Not accessible"

def list_skills():
    """List loaded skills from the skills/ directory."""
    from skills.skill_loader import load_skills
    # Mock engines for loader
    skills = load_skills(None, None, None)
    if skills:
        return f"{TICK} Skills Loaded: {', '.join(skills.keys())}"
    return f"{WARN} Skills: None found in skills/"

def run_checks():
    print(f"\n{YELLOW}=== {config.MANU_NAME} SYSTEM HEALTH CHECK ==={RESET}\n")
    
    # Core Dependencies
    print("--- Core Dependencies ---")
    deps = ["speech_recognition", "pyaudio", "faster_whisper", "pyttsx3", "ollama", "cv2", "PIL", "pyperclip", "psutil"]
    for d in deps: print(check_module(d))
    
    # New Task Dependencies
    print("\n--- Advanced Features ---")
    adv = ["pygame", "pystray", "deepface", "face_recognition", "OpenGL", "pyautogui"]
    for a in adv: print(check_module(a))
    
    # Hardware & Services
    print("\n--- Hardware & Services ---")
    print(check_mic())
    print(check_camera())
    print(check_ollama())
    
    # Skills
    print("\n--- Skill Registry ---")
    try:
        print(list_skills())
    except Exception as e:
        print(f"{CROSS} Skills error: {e}")

    # Directories
    print("\n--- Data Directories ---")
    for folder in ["logs", "voice_notes", "screenshots", "captures", "security", "skills"]:
        path = config.DATA_DIR / folder
        if path.exists():
            print(f"{TICK} {folder}/")
        else:
            print(f"{CROSS} {folder}/ (Missing)")

    print(f"\n{YELLOW}Ready to launch? Run 'python main.py'{RESET}\n")

if __name__ == "__main__":
    run_checks()
