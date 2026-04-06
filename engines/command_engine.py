import os
import subprocess
import webbrowser
import datetime
import re
import psutil
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

from PIL import ImageGrab
import config

from modules.clipboard_ai import ClipboardAI
from modules.voice_notes import VoiceNotesManager
from modules.screen_reader import ScreenReader
from modules.daily_briefing import DailyBriefing
from skills.skill_loader import load_skills, try_skills

class CommandEngine:
    def __init__(self, tts, memory, brain):
        self.tts = tts
        self.memory = memory
        self.brain = brain
        
        # Phase 4 Managers
        self.clipboard = ClipboardAI(brain, tts)
        self.voice_notes = VoiceNotesManager(brain, tts, config.DATA_DIR)
        self.screen_reader = ScreenReader(brain, tts)
        self.briefing = DailyBriefing(memory)
        
        self._skills = {}
        if config.AUTO_LOAD_SKILLS:
            self._skills = load_skills(self.tts, self.memory, self.brain)

    def execute_command(self, text):
        """Parse intent and return response string."""
        text = text.lower().strip()
        
        # APP SHORTCUTS
        APP_SHORTCUTS = {
          "youtube": "https://youtube.com", "google": "https://google.com",
          "notepad": "notepad", "calculator": "calc",
          "file explorer": "explorer", "task manager": "taskmgr",
          "settings": "ms-settings:", "gmail": "https://mail.google.com",
          "github": "https://github.com", "spotify": "spotify"
        }
        
        # SLEEP/LOCK / HIBERNATE
        if any(k in text for k in ["lock session", "lock manu", "exit mode"]):
            return "LOCKED"
            
        if "hibernate" in text or "shut down" in text:
            os.system("shutdown /h")
            return "Hibernating system..."

        # CLIPBOARD AI (Task 2)
        if "clipboard" in text or "explain this" in text or "summarize this" in text:
            mode = "summarize" if "summarize" in text else "explain"
            if "translate" in text: mode = f"translate to {text.split('to')[-1].strip()}"
            return self.clipboard.get_and_process(mode)

        # VOICE NOTES (Task 2)
        if "start a voice note" in text or "take a note" in text:
            content = text.replace("start a voice note", "").replace("take a note", "").strip()
            if not content: return "Please tell me what to note down."
            return self.voice_notes.save_note(content)
        
        if "list my notes" in text:
            return self.voice_notes.list_notes()
        
        if "read my last note" in text:
            return self.voice_notes.read_last_note()

        # SCREEN READER (Task 2)
        if "on my screen" in text or "describe my screen" in text:
            return self.screen_reader.describe_screen()
        
        if "window title" in text:
            return f"You are currently in {self.screen_reader.get_active_window_title()}."

        # MORNING BRIEFING (Task 2)
        if any(k in text for k in ["morning briefing", "brief me", "daily summary"]):
            user_name = self.memory.get_setting("user_name", config.USER_NAME)
            return self.briefing.generate(user_name)

        # PYAUTOGUI / OS CONTROL (Task 2)
        if text.startswith("type "):
            if HAS_PYAUTOGUI:
                pyautogui.write(text[5:])
                return "Typed successfully."
            return "Install pyautogui for typing support."
        
        if "press " in text and ("key" in text or "enter" in text):
            if HAS_PYAUTOGUI:
                key = text.split("press ")[-1].replace("key", "").strip()
                pyautogui.press(key)
                return f"Pressed {key}."
            return "Install pyautogui for keypress support."

        # MATH / UNIT CONVERSION (Task 2)
        if "calculate" in text or "=" in text:
            try:
                expr = text.replace("calculate", "").replace("=", "").strip()
                # Safe eval for basic math
                return f"Result: {eval(expr, {'__builtins__': None}, {'math': __import__('math')})}"
            except:
                pass # Let brain handle complex math

        # TIME/DATE
        if any(k in text for k in ["what time is it", "current time", "time now"]):
            return datetime.datetime.now().strftime("%I:%M %p on %A, %B %d")
            
        # SYSTEM INFO
        if any(k in text for k in ["system info", "how's the cpu", "system status"]):
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            batt = psutil.sensors_battery()
            batt_str = f"{batt.percent}%" if batt else "N/A"
            return f"CPU: {cpu}% | RAM: {mem}% | Battery: {batt_str}."

        # REMINDERS
        rem_match = re.match(r"(?:set reminder|remind me to)\s+(.+?)\s+(?:at|in)\s+(.+)", text)
        if rem_match:
            task, time_str = rem_match.groups()
            # Simple time parse for "in X minutes"
            remind_at = datetime.datetime.now()
            if "minute" in time_str:
                mins = int(re.search(r"(\d+)", time_str).group(1))
                remind_at += datetime.timedelta(minutes=mins)
            self.memory.add_reminder(task, remind_at.isoformat())
            return f"Reminder set: {task} at {remind_at.strftime('%H:%M')}."

        if "list reminders" in text or "my reminders" in text:
            rems = self.memory.list_reminders()
            if not rems: return "No pending reminders."
            return "Pending: " + ", ".join([f"{r['title']} ({r['remind_at']})" for r in rems])

        # SEARCH / GOOGLE
        search_match = re.match(r"(?:search|google|look up)\s+(.+)", text)
        if search_match:
            query = search_match.group(1)
            webbrowser.open(f"https://google.com/search?q={query}")
            return f"Searching Google for {query}."

        # YOUTUBE
        if text.startswith("play ") and "on youtube" in text:
            song = text.replace("play ", "").replace("on youtube", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
            return f"Playing {song} on YouTube."

        # NOTES
        note_match = re.match(r"(?:note that|take a note)\s+(.+)", text)
        if note_match:
            content = note_match.group(1)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = config.DATA_DIR / "notes" / f"note_{ts}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return "Note recorded."

        # SCREENSHOT
        if "screenshot" in text:
            ts = datetime.datetime.now().strftime("%H%M%S")
            path = config.DATA_DIR / "screenshots" / f"shot_{ts}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            ImageGrab.grab().save(path)
            return f"Screenshot saved to data/screenshots/."

        # VOLUME
        vol_match = re.search(r"volume (\d+)", text)
        if vol_match:
            return self._set_volume(int(vol_match.group(1)))
        if "volume up" in text: return self._set_volume("up")
        if "volume down" in text: return self._set_volume("down")

        # APPS
        if text.startswith("open "):
            app = text.replace("open ", "").strip()
            if app in APP_SHORTCUTS:
                target = APP_SHORTCUTS[app]
                try:
                    os.startfile(target) if os.name == 'nt' else subprocess.run(["open", target])
                    return f"Opening {app}."
                except:
                    webbrowser.open(target)
                    return f"Opening {app} in browser."

        # SKILLS
        skill_res = try_skills(self._skills, text)
        if skill_res: return skill_res

        return None # Fallback to LLM

    def _set_volume(self, action):
        try:
            import ctypes
            # Simplified Windows logic using pycaw if possible
            if os.name == 'nt':
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
                current = volume.GetMasterVolumeLevelScalar()
                if action == "up": volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
                elif action == "down": volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
                elif isinstance(action, int): volume.SetMasterVolumeLevelScalar(action / 100, None)
                return "Volume adjusted."
        except:
            pass
        return "I couldn't adjust the system volume."
