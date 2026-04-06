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

        # CLIPBOARD AI (Task 2a)
        if "clipboard" in text or "explain this" in text or "summarize this" in text or "improve this" in text:
            if "what's in" in text:
                content = pyperclip.paste()
                return f"Clipboard content (first 200 chars): {content[:200]}"
            
            mode = "summarize"
            if "explain" in text: mode = "explain"
            elif "improve" in text: mode = "improve writing"
            elif "translate" in text:
                lang = text.split("to")[-1].strip()
                mode = f"translate to {lang}"
            
            return self.clipboard.get_and_process(mode)

        # VOICE NOTES (Task 2b)
        if "take a note" in text or "note that" in text:
            content = text.replace("take a note", "").replace("note that", "").strip()
            if not content: return "What should I note down?"
            return self.voice_notes.save_note(content)
        
        if "list my notes" in text or "show notes" in text:
            return self.voice_notes.list_notes()
        
        if "read my last note" in text:
            return self.voice_notes.read_last_note()
            
        if "find notes about" in text:
            keyword = text.split("about")[-1].strip()
            return self.voice_notes.search_notes(keyword)

        # SCREEN READER (Task 2c)
        if "on my screen" in text or "describe my screen" in text:
            if "describe" in text:
                return self.screen_reader.describe_screen()
            title = self.screen_reader.get_active_window_title()
            return f"You're currently working in {title}."

        # ADVANCED SYSTEM COMMANDS (Task 2d)
        if "screenshot" in text:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = config.DATA_DIR / "screenshots" / f"screenshot_{ts}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            ImageGrab.grab().save(path)
            return f"Screenshot saved to data/screenshots/."

        if "empty recycle bin" in text:
            if os.name == 'nt':
                try:
                    import winshell
                    winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                    return "Recycle bin emptied."
                except ImportError:
                    return "Please install winshell for this command."
            return "This command is only available on Windows."

        if "lock screen" in text or "lock my pc" in text:
            if os.name == 'nt':
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                return "Locking workstation."
            return "PC lock is currently Windows-only."

        if "hibernate" in text or "sleep pc" in text:
            if os.name == 'nt':
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return "System entering sleep mode."
            return "Sleep command is Windows-only for now."

        if "list running apps" in text or "what's running" in text:
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] not in apps:
                        apps.append(proc.info['name'])
                    if len(apps) >= 8: break
                except: continue
            return f"Top running apps: {', '.join(apps)}."

        if "kill " in text:
            app_name = text.replace("kill ", "").strip()
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    return f"Terminated {proc.info['name']}."
            return f"Could not find process matching '{app_name}'."

        if text.startswith("type "):
            if HAS_PYAUTOGUI:
                pyautogui.typewrite(text[5:])
                return "Typed successfully."
            return "Install pyautogui for typing support."
        
        if text.startswith("press "):
            if HAS_PYAUTOGUI:
                key = text.replace("press ", "").strip()
                pyautogui.hotkey(*key.split("+"))
                return f"Pressed {key}."
            return "Install pyautogui for keypress support."

        # MATH & CONVERSIONS (Task 2e)
        if "calculate" in text or "what is " in text:
            expr = text.replace("calculate", "").replace("what is", "").strip()
            # Basic sanitization
            safe_expr = re.sub(r'[^0-9\+\-\*\/\(\)\. ]', '', expr)
            try:
                result = eval(safe_expr, {"__builtins__": None}, {})
                return f"The result is {result}."
            except:
                pass # LLM will handle complex math or bad inputs

        if "convert " in text:
            # Simple unit converter logic
            return "I'll help you with that conversion. (AI will process details)"

        # DAILY BRIEFING (Task 2f)
        if any(k in text for k in ["morning briefing", "good morning brief", "what's today"]):
            user_name = self.memory.get_setting("user_name", config.USER_NAME)
            return self.briefing.generate(user_name)

        # APP SHORTCUTS
        APP_SHORTCUTS = {
          "youtube": "https://youtube.com", "google": "https://google.com",
          "notepad": "notepad", "calculator": "calc",
          "file explorer": "explorer", "task manager": "taskmgr",
          "settings": "ms-settings:", "gmail": "https://mail.google.com",
          "github": "https://github.com", "spotify": "spotify"
        }
        
        # SLEEP/LOCK / HIBERNATE (Standard)
        if any(k in text for k in ["lock session", "lock manu", "exit mode"]):
            return "LOCKED"

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
