import os
import subprocess
import webbrowser
import datetime
import re
import psutil
import pyperclip
from pathlib import Path
from PIL import ImageGrab
import importlib.util
import config

class CommandEngine:
    def __init__(self, memory):
        self.memory = memory
        self._skills = []
        if config.AUTO_LOAD_SKILLS:
            self._load_skills()

    def _load_skills(self):
        """Scan skills folder for skill_*.py files and instantiate Skill_* classes."""
        skills_dir = Path(__file__).parent.parent / "skills"
        if not skills_dir.exists():
            return
            
        for file in skills_dir.glob("skill_*.py"):
            module_name = f"skills.{file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find all classes that start with Skill_
                for name, obj in vars(module).items():
                    if name.startswith("Skill_") and isinstance(obj, type):
                        self._skills.append(obj(self.memory))
                        print(f"✅ Loaded skill: {name}")
            except Exception as e:
                print(f"❌ Failed to load skill from {file.name}: {e}")

    def execute_command(self, text):
        """Parse intent and return response string."""
        text = text.lower().strip()
        
        # SLEEP/LOCK
        if any(k in text for k in ["enter sleep mode", "sleep mode", "lock session"]):
            return "LOCKED"
            
        # COMPLIMENT
        if any(k in text for k in ["thank you", "thanks", "great job", "well done"]):
            return "You're very welcome! I'm happy to help."
            
        # JOKE
        if any(k in text for k in ["joke", "make me laugh", "tell me a joke"]):
            # Handled by emotion manager or local list
            return None # Fallback to LLM or personality trigger
            
        # TIME
        if any(k in text for k in ["what time", "current time", "what's the time"]):
            now = datetime.datetime.now()
            return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."
            
        # DATE
        if any(k in text for k in ["what day", "today's date", "what's today"]):
            now = datetime.datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}."
            
        # BATTERY
        if any(k in text for k in ["battery", "charge level", "power level"]):
            battery = psutil.sensors_battery()
            if battery:
                pct = battery.percent
                plugged = "plugged in" if battery.power_plugged else "on battery"
                comment = "I'm feeling fully charged!" if pct > 90 else "I'm doing fine." if pct > 20 else "I'm getting a bit hungry for power."
                return f"My battery is at {pct}%, and I'm currently {plugged}. {comment}"
            return "I can't seem to find my battery sensors."

        # SYSTEM INFO
        if any(k in text for k in ["system info", "system status", "cpu", "memory usage"]):
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            return f"System status: CPU at {cpu}%, Memory at {mem}%, and Disk at {disk}% usage."

        # VOLUME
        vol_match = re.search(r"(?:set volume|volume) (?:to )?(\d+)", text)
        if vol_match:
            return self._set_volume(int(vol_match.group(1)))
        if any(k in text for k in ["volume up", "louder", "turn up"]):
            return self._volume_up()
        if any(k in text for k in ["volume down", "quieter", "turn down"]):
            return self._volume_down()
        if any(k in text for k in ["mute", "silence"]):
            return self._mute()

        # BRIGHTNESS
        bright_match = re.search(r"brightness (?:to )?(\d+)", text)
        if bright_match:
            return self._set_brightness(int(bright_match.group(1)))

        # OPEN APP/URL
        open_match = re.match(r"(?:open|launch|start|run|go to)\s+(.+)", text)
        if open_match:
            query = open_match.group(1).strip()
            if query in config.APP_SHORTCUTS:
                target = config.APP_SHORTCUTS[query]
                if target.startswith("http"):
                    webbrowser.open(target)
                    return f"Opening {query} in your browser."
                else:
                    try:
                        os.startfile(target) if os.name == 'nt' else subprocess.run([target])
                        return f"Launching {query}."
                    except Exception as e:
                        return f"I couldn't launch {query}. Error: {e}"
            else:
                # Direct URL check
                if "." in query and " " not in query:
                    url = f"https://{query}" if not query.startswith("http") else query
                    webbrowser.open(url)
                    return f"Heading over to {query}."

        # WEB SEARCH
        search_match = re.match(r"(?:search|google|look up|search for)\s+(.+)", text)
        if search_match:
            query = search_match.group(1).strip()
            if "youtube" in text:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                return f"Searching YouTube for {query}."
            else:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching Google for {query}."

        # PLAY MUSIC
        if text.startswith("play "):
            query = text[5:].strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}+music")
            return f"Playing {query} music on YouTube."

        # NOTE
        if any(text.startswith(k) for k in ["take a note", "note that", "write down"]):
            content = text
            for k in ["take a note", "note that", "write down"]:
                if text.startswith(k):
                    content = text[len(k):].strip()
                    break
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            note_file = config.DATA_DIR / f"note_{timestamp}.txt"
            note_file.write_text(content, encoding="utf-8")
            return f"Note saved to {note_file.name}."

        # REMINDER
        if any(text.startswith(k) for k in ["remind me to", "set a reminder"]):
            # Basic reminder parsing
            match = re.match(r"(?:remind me to|set a reminder)\s+(.+?)\s+(?:at|in|on)\s+(.+)", text)
            if match:
                task, time_str = match.groups()
                # Dummy parsing for time_str (actual time parsing would be more complex)
                # We'll just store the string for now or use relative minutes
                remind_at = datetime.datetime.now() + datetime.timedelta(minutes=30) # Default
                if "minute" in time_str:
                    mins = re.search(r"(\d+)", time_str)
                    if mins: remind_at = datetime.datetime.now() + datetime.timedelta(minutes=int(mins.group(1)))
                
                self.memory.add_reminder(task, remind_at.isoformat())
                return f"Got it. I'll remind you to {task} at {remind_at.strftime('%I:%M %p')}."

        # LIST REMINDERS
        if any(k in text for k in ["list reminders", "my reminders"]):
            reminders = self.memory.list_reminders()
            if not reminders: return "You have no pending reminders."
            msg = "Here are your reminders:\n"
            for r in reminders:
                msg += f"- {r['title']} (at {r['remind_at']})\n"
            return msg

        # SCREENSHOT
        if any(k in text for k in ["screenshot", "screen capture"]):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = config.DATA_DIR / f"screenshot_{timestamp}.png"
            ImageGrab.grab().save(path)
            return f"Screenshot saved as {path.name}."

        # MEMORY SEARCH
        if any(text.startswith(k) for k in ["do you remember", "recall"]):
            keyword = text.split(" ", 3)[-1]
            results = self.memory.search_memory(keyword)
            if results:
                msg = f"I found {len(results)} items matching '{keyword}':\n"
                for r in results[:3]:
                    msg += f"- [{r['timestamp']}] {r['message']}\n"
                return msg
            return f"I don't recall anything about '{keyword}'."

        # YESTERDAY SUMMARY
        if any(k in text for k in ["summarize yesterday", "yesterday's chat"]):
            return self.memory.summarize_yesterday()

        # SKILL PLUGINS
        for skill in self._skills:
            if skill.can_handle(text):
                return skill.handle(text)

        return None # Fallback to LLM

    def _set_volume(self, level):
        level = max(0, min(100, level))
        try:
            if os.name == 'nt':
                # Simplified volume control via NirCmd if available, or just psutil alert
                # Real programmatic control for Windows uses pycaw
                try:
                    import ctypes
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    from comtypes import CLSCTX_ALL
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
                    volume.SetMasterVolumeLevelScalar(level / 100, None)
                    return f"Volume set to {level}%."
                except ImportError:
                    return f"Volume set to {level}% (UI only, pycaw needed for system)."
        except Exception as e:
            return f"I couldn't change the volume. Error: {e}"

    def _volume_up(self): return self._set_volume(75) # Simplified
    def _volume_down(self): return self._set_volume(25) # Simplified
    def _mute(self): return self._set_volume(0)

    def _set_brightness(self, level):
        level = max(0, min(100, level))
        try:
            if os.name == 'nt':
                import wmi
                wmi.WMI(namespace='wmi').WmiMonitorBrightnessMethods()[0].WmiSetBrightness(level, 0)
                return f"Brightness set to {level}%."
        except Exception:
            return "I can't control brightness on this machine."
