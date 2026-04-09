import os
import subprocess
import webbrowser
import datetime
import re
import psutil
from pathlib import Path
import config

# Optional imports
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

try:
    from PIL import ImageGrab
    HAS_IMAGEGRAB = True
except ImportError:
    HAS_IMAGEGRAB = False

class CommandEngine:
    def __init__(self, brain, tts, memory, skills={}):
        self.brain = brain
        self.tts = tts
        self.memory = memory
        self.skills = skills

    def execute_command(self, text):
        """Parse intent and execute task (Upgrade 5)."""
        text = text.lower().strip()
        
        # 1. TIME/DATE
        if re.search(r"\b(time|what time)\b", text):
            return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."
        if re.search(r"\b(date|today|what day)\b", text):
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

        # 2. BATTERY
        if "battery" in text or "charge level" in text:
            batt = psutil.sensors_battery()
            if not batt: return "I'm not sensing a battery on this system."
            status = "charging" if batt.power_plugged else "discharging"
            return f"Your battery is at {batt.percent}% and is currently {status}."

        # 3. SYSTEM INFO
        if any(k in text for k in ["system info", "cpu", "memory", "ram"]):
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            return f"System Status - CPU: {cpu}%, RAM: {mem}%, Disk: {disk}% used."

        # 4. OPEN APPS
        if text.startswith(("open ", "launch ")):
            app = text.replace("open ", "").replace("launch ", "").strip()
            APP_MAP = {
                "youtube": "https://youtube.com",
                "google": "https://google.com",
                "gmail": "https://mail.google.com",
                "github": "https://github.com",
                "notepad": "notepad",
                "calculator": "calc",
                "explorer": "explorer",
                "settings": "ms-settings:",
                "browser": "https://google.com"
            }
            if app in APP_MAP:
                target = APP_MAP[app]
                try:
                    if target.startswith("http"):
                        webbrowser.open(target)
                    else:
                        subprocess.Popen(target, shell=True)
                    return f"Opening {app} right now."
                except Exception as e:
                    return f"Failed to launch {app}: {e}"

        # 5. SEARCH / PLAY
        search_match = re.search(r"(?:search|google)\s+(.+)", text)
        if search_match:
            query = search_match.group(1)
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"Searching Google for {query}."

        play_match = re.search(r"play\s+(.+)\son\s+youtube", text)
        if play_match:
            query = play_match.group(1)
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return f"Playing {query} on YouTube."

        # 6. VOLUME
        if "volume up" in text:
            self._adjust_volume("up")
            return "Volume increased."
        if "volume down" in text:
            self._adjust_volume("down")
            return "Volume decreased."
        if "mute" in text:
            self._adjust_volume("mute")
            return "Volume muted."
        
        vol_match = re.search(r"set volume to (\d+)", text)
        if vol_match:
            val = int(vol_match.group(1))
            self._adjust_volume(val)
            return f"Volume set to {val}%."

        # 7. NOTES & REMINDERS
        if text.startswith("take a note"):
            content = text.replace("take a note", "").strip()
            if not content: return "What should I note down?"
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            note_path = config.DATA_DIR / "notes" / f"note_{ts}.txt"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            with open(note_path, "w") as f:
                f.write(content)
            return "Note saved successfully."

        # REMINDERS
        rem_match = re.match(r"(?:set reminder|remind me to)\s+(.+?)\s+(?:at|in)\s+(.+)", text)
        if rem_match:
            task, time_phrase = rem_match.groups()
            dt = self._parse_time(time_phrase)
            if dt:
                self.memory.add_reminder(task, dt.isoformat())
                return f"Reminder set: '{task}' at {dt.strftime('%H:%M %p')}."
            return "I couldn't parse the time for that reminder."

        if "list reminders" in text:
            rems = self.memory.get_due_reminders() # Just an example, maybe list_all
            return f"You have {len(rems)} pending reminders."

        # 8. UTILS
        if "joke" in text:
            return "TELL_JOKE" # Handled by emotion react in main
        
        if "screenshot" in text:
            if not HAS_IMAGEGRAB: return "Image library missing."
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = config.DATA_DIR / "screenshots" / f"shot_{ts}.png"
            img_path.parent.mkdir(parents=True, exist_ok=True)
            ImageGrab.grab().save(img_path)
            return f"Screenshot saved to data/screenshots/."

        if "read clipboard" in text:
            if not HAS_CLIPBOARD: return "Clipboard library not installed."
            return f"Clipboard contains: {pyperclip.paste()}"

        if "summarize yesterday" in text:
            return self.memory.summarize_yesterday()
        
        if "last message" in text:
            last = self.memory.get_last_user_message()
            return f"Your last message was: '{last}'" if last else "I don't recall any messages yet."

        if any(k in text for k in ["sleep mode", "lock manu"]):
            return "SLEEP_MODE"

        # 9. SKILLS (Upgrade 10 logic)
        for name, skill in self.skills.items():
            if skill.can_handle(text):
                return skill.handle(text)

        return None # Falls back to LLM

    def _adjust_volume(self, action):
        """Cross-platform volume control placeholder."""
        try:
            if os.name == 'nt':
                # Simplified Windows logic
                if action == "up": subprocess.run(["nircmd.exe", "changesysvolume", "2000"], capture_output=True)
                elif action == "down": subprocess.run(["nircmd.exe", "changesysvolume", "-2000"], capture_output=True)
                elif isinstance(action, int): pass # would need exact calc
            else:
                if action == "up": subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "10%+"])
                elif action == "down": subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "10%-"])
        except: pass

    def _parse_time(self, phrase):
        """Rudimentary time parser (Task 5)."""
        now = datetime.datetime.now()
        phrase = phrase.strip()
        
        # 'in 30 minutes'
        in_match = re.search(r"in (\d+) (minute|hour)", phrase)
        if in_match:
            count = int(in_match.group(1))
            unit = in_match.group(2)
            if "minute" in unit: return now + datetime.timedelta(minutes=count)
            if "hour" in unit: return now + datetime.timedelta(hours=count)
        
        # 'at 8 PM'
        at_match = re.search(r"at (\d+)(?::(\d+))?\s*(am|pm)?", phrase, re.I)
        if at_match:
            h = int(at_match.group(1))
            m = int(at_match.group(2)) if at_match.group(2) else 0
            meridiem = at_match.group(3).lower() if at_match.group(3) else None
            
            if meridiem == "pm" and h < 12: h += 12
            elif meridiem == "am" and h == 12: h = 0
            
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target < now: target += datetime.timedelta(days=1)
            return target
            
        return None
