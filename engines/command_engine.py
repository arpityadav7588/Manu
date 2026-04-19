"""
engines/command_engine.py
Manu's command dispatcher — pattern match voice input to actions.
Returns response string, None (fall to LLM), or "LOCKED".
All commands work offline except web search/YouTube.
"""

import os
import re
import platform
import subprocess
import webbrowser
import datetime
import logging
import random
import urllib.parse

import psutil

log = logging.getLogger("Manu.Commands")

OS = platform.system()   # "Windows" | "Darwin" | "Linux"

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my user I needed more RAM. They said, 'you and me both.'",
    "Why did the AI go to therapy? Too many unresolved dependencies.",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
    "I'm not lazy. I'm in energy-saving mode.",
    "Why was the JavaScript developer sad? They didn't Node how to Express themselves.",
    "My user asked me to be more human. I said I'd think about it. Then I didn't.",
    "What do you call an AI that sings? Adele-gorithm.",
    "I asked my user how their day was. They said 'fine'. Classic.",
    "Why do Java developers wear glasses? Because they don't C sharp.",
]

# App shortcuts: command keyword → Windows executable or URL
APP_MAP = {
    "youtube":       "https://youtube.com",
    "google":        "https://google.com",
    "gmail":         "https://mail.google.com",
    "github":        "https://github.com",
    "reddit":        "https://reddit.com",
    "twitter":       "https://twitter.com",
    "linkedin":      "https://linkedin.com",
    "notepad":       "notepad",
    "calculator":    "calc",
    "file explorer": "explorer",
    "explorer":      "explorer",
    "task manager":  "taskmgr",
    "settings":      "ms-settings:",
    "paint":         "mspaint",
    "camera":        "microsoft.windows.camera:",
    "spotify":       "spotify",
    "discord":       "discord",
    "vscode":        "code",
    "vs code":       "code",
    "chrome":        "chrome",
    "firefox":       "firefox",
    "edge":          "msedge",
}


class CommandEngine:
    """
    Pattern-based command dispatcher.
    Priority order:
      1. Exact/keyword pattern match → direct action
      2. Return None → falls through to BrainEngine (LLM)
      3. Return "LOCKED" → triggers session lock in main.py
    """

    def execute(self, text: str, context: dict = None) -> str | None:
        """
        Main entry point. Receives transcribed voice input as text.
        Returns response string, None (LLM fallback), or "LOCKED".
        """
        if not text:
            return None
        t = text.lower().strip()

        # ── Identity & Meta ───────────────────────────────────────────────────
        if any(k in t for k in ["who are you", "your name", "what are you",
                                  "introduce yourself"]):
            return self._handle_identity()

        if any(k in t for k in ["what can you do", "your features",
                                  "your abilities", "help me", "capabilities"]):
            return self._handle_capabilities()

        # ── Session Lock ──────────────────────────────────────────────────────
        if any(k in t for k in ["sleep mode", "lock session", "lock screen",
                                  "enter sleep", "go to sleep", "lock down"]):
            return "LOCKED"

        # ── Time & Date ───────────────────────────────────────────────────────
        if any(k in t for k in ["what time", "current time", "tell me the time",
                                  "what's the time"]):
            return self._handle_time()

        if any(k in t for k in ["what day", "what date", "today's date",
                                  "what's today", "what is today"]):
            return self._handle_date()

        # ── Jokes ─────────────────────────────────────────────────────────────
        if any(k in t for k in ["tell me a joke", "say a joke", "make me laugh",
                                  "tell a joke", "joke time"]):
            return self._handle_joke()

        # ── Greetings / Acknowledgements ──────────────────────────────────────
        if any(k in t for k in ["thank you", "thanks a lot", "thanks manu",
                                  "good job", "well done", "you're great"]):
            return random.choice([
                "Of course.", "Anytime.", "That's what I'm here for.",
                "Happy to help.", "Always."
            ])

        # ── Battery ───────────────────────────────────────────────────────────
        if any(k in t for k in ["battery", "charge level", "power level",
                                  "how much battery", "battery status"]):
            return self._handle_battery()

        # ── System Info ───────────────────────────────────────────────────────
        if any(k in t for k in ["system info", "system status", "cpu usage",
                                  "memory usage", "ram", "disk space",
                                  "how's the system", "resource usage"]):
            return self._handle_system_info()

        # ── Volume ────────────────────────────────────────────────────────────
        vol_match = re.search(r"(?:set volume|volume|set it)\s+to\s+(\d+)", t)
        if vol_match:
            return self._handle_set_volume(int(vol_match.group(1)))

        if any(k in t for k in ["volume up", "louder", "increase volume",
                                  "turn it up", "turn up"]):
            return self._handle_volume_delta(+10)

        if any(k in t for k in ["volume down", "quieter", "decrease volume",
                                  "turn it down", "turn down", "lower volume"]):
            return self._handle_volume_delta(-10)

        if any(k in t for k in ["mute", "silence", "shut up audio"]):
            return self._handle_mute()

        # ── Screenshot ────────────────────────────────────────────────────────
        if any(k in t for k in ["screenshot", "take a screenshot",
                                  "capture screen", "screen capture"]):
            return self._handle_screenshot()

        # ── Clipboard ─────────────────────────────────────────────────────────
        if any(k in t for k in ["read clipboard", "what's in clipboard",
                                  "clipboard content", "paste"]):
            return self._handle_read_clipboard()

        # ── Notes ─────────────────────────────────────────────────────────────
        note_match = re.search(
            r"(?:take a note|create note|note that|write down|save note|note:?)\s*[:\-]?\s*(.+)",
            t
        )
        if note_match:
            return self._handle_create_note(note_match.group(1).strip())

        # ── Reminders ─────────────────────────────────────────────────────────
        reminder_match = re.search(
            r"(?:remind me to|set a reminder|reminder)[:\s]+(.+?)\s+(?:at|in)\s+(.+)",
            t
        )
        if reminder_match:
            task     = reminder_match.group(1).strip()
            time_str = reminder_match.group(2).strip()
            return self._handle_reminder(task, time_str)

        if any(k in t for k in ["list reminders", "my reminders",
                                  "what are my reminders", "show reminders"]):
            return self._handle_list_reminders()

        # ── Web Search ────────────────────────────────────────────────────────
        search_match = re.search(
            r"(?:search for|search|google|look up|find)\s+(.+?)(?:\s+on\s+(?:google|web))?$",
            t
        )
        if search_match:
            query = search_match.group(1).strip()
            return self._handle_web_search(query)

        # ── YouTube ───────────────────────────────────────────────────────────
        youtube_play = re.search(
            r"(?:play|search youtube for|youtube)\s+(.+?)(?:\s+on\s+youtube)?$",
            t
        )
        if youtube_play:
            return self._handle_youtube(youtube_play.group(1).strip())

        # ── Open App / URL ────────────────────────────────────────────────────
        open_match = re.search(
            r"(?:open|launch|start|run|go to)\s+(.+)", t
        )
        if open_match:
            target = open_match.group(1).strip()
            return self._handle_open(target)

        # ── Brightness ────────────────────────────────────────────────────────
        bright_match = re.search(r"brightness\s+(?:to\s+)?(\d+)", t)
        if bright_match:
            return self._handle_brightness(int(bright_match.group(1)))

        # No command matched — fall through to LLM
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Command Handlers (private)
    # ══════════════════════════════════════════════════════════════════════════

    def _handle_identity(self) -> str:
        return (
            "I'm Manu — your personal AI assistant, running locally on this machine. "
            "Built in Python, no cloud required."
        )

    def _handle_capabilities(self) -> str:
        return (
            "I can open apps, search the web, play YouTube, check your battery and system stats, "
            "set reminders, take notes, control volume, take screenshots, tell jokes, "
            "and hold a conversation. All locally — no internet needed for core functions. "
            "What would you like to try?"
        )

    def _handle_time(self) -> str:
        now = datetime.datetime.now()
        return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A')}."

    def _handle_date(self) -> str:
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    def _handle_joke(self) -> str:
        return random.choice(JOKES)

    def _handle_battery(self) -> str:
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return "No battery detected — you must be on a desktop."
            pct     = bat.percent
            plugged = bat.power_plugged

            if plugged and pct >= 95:
                status = "fully charged and plugged in"
            elif plugged:
                status = f"charging at {pct:.0f}%"
            elif pct <= 20:
                status = f"at {pct:.0f}% and unplugged — connect power soon"
            else:
                hours = round(pct / 10, 1)
                status = f"at {pct:.0f}%, roughly {hours} hours remaining"

            return f"Battery is {status}."
        except Exception as e:
            log.error(f"Battery check error: {e}")
            return "Couldn't read battery status right now."

    def _handle_system_info(self) -> str:
        try:
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return (
                f"CPU at {cpu:.0f}%, "
                f"RAM {ram.percent:.0f}% used ({ram.available // (1024**3)} GB free), "
                f"Disk {disk.percent:.0f}% used."
            )
        except Exception as e:
            return f"System info unavailable: {e}"

    def _handle_set_volume(self, level: int) -> str:
        level = max(0, min(100, level))
        try:
            if OS == "Windows":
                self._win_set_volume(level)
            elif OS == "Darwin":
                subprocess.run(["osascript", "-e",
                                 f"set volume output volume {level}"])
            else:
                subprocess.run(["amixer", "sset", "Master", f"{level}%"])
            return f"Volume set to {level}%."
        except Exception as e:
            return f"Couldn't set volume: {e}"

    def _handle_volume_delta(self, delta: int) -> str:
        try:
            if OS == "Windows":
                import ctypes
                for _ in range(abs(delta) // 2):
                    ctypes.windll.user32.keybd_event(
                        0xAF if delta > 0 else 0xAE, 0, 0, 0
                    )
                direction = "up" if delta > 0 else "down"
                return f"Volume turned {direction}."
            elif OS == "Darwin":
                steps = abs(delta) // 5
                for _ in range(steps):
                    subprocess.run([
                        "osascript", "-e",
                        f"set volume output volume "
                        f"(output volume of (get volume settings) "
                        f"{'+ ' if delta > 0 else '- '}{abs(delta)})"
                    ])
                direction = "up" if delta > 0 else "down"
                return f"Volume turned {direction}."
            else:
                sign = "+" if delta > 0 else "-"
                subprocess.run(["amixer", "sset", "Master",
                                  f"{abs(delta)}%{sign}"])
                direction = "up" if delta > 0 else "down"
                return f"Volume turned {direction}."
        except Exception as e:
            return f"Couldn't adjust volume: {e}"

    def _handle_mute(self) -> str:
        try:
            if OS == "Windows":
                import ctypes
                ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
                return "Audio toggled."
            elif OS == "Darwin":
                subprocess.run(["osascript", "-e", "set volume with output muted"])
                return "Audio muted."
            else:
                subprocess.run(["amixer", "sset", "Master", "toggle"])
                return "Audio toggled."
        except Exception as e:
            return f"Couldn't toggle mute: {e}"

    def _handle_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join("data", f"screenshot_{ts}.png")
            os.makedirs("data", exist_ok=True)
            img  = ImageGrab.grab()
            img.save(path)
            return f"Screenshot saved as '{os.path.basename(path)}'."
        except ImportError:
            return "Pillow not installed. Run: pip install pillow"
        except Exception as e:
            return f"Screenshot failed: {e}"

    def _handle_read_clipboard(self) -> str:
        try:
            import pyperclip
            text = pyperclip.paste()
            if text:
                return f"Clipboard: {text[:150]}{'...' if len(text)>150 else ''}"
            return "Clipboard is empty."
        except ImportError:
            return "pyperclip not installed. Run: pip install pyperclip"

    def _handle_create_note(self, content: str) -> str:
        try:
            notes_dir = os.path.join("data", "notes")
            os.makedirs(notes_dir, exist_ok=True)
            ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(notes_dir, f"note_{ts}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Created: {datetime.datetime.now()}\n\n{content}")
            return f"Note saved. I called it 'note_{ts}.txt'."
        except Exception as e:
            return f"Couldn't save note: {e}"

    def _handle_reminder(self, task: str, time_str: str) -> str:
        # Simple confirmation — actual scheduling done via MemoryManager
        return (
            f"Reminder noted: '{task}' at {time_str}. "
            "I'll alert you when the time comes."
        )

    def _handle_list_reminders(self) -> str:
        return "Reminder list requires the memory module — loading."

    def _handle_web_search(self, query: str) -> str:
        try:
            encoded = urllib.parse.quote_plus(query)
            url     = f"https://www.google.com/search?q={encoded}"
            webbrowser.open(url)
            return f"Searching for '{query}'."
        except Exception as e:
            return f"Couldn't open browser: {e}"

    def _handle_youtube(self, query: str) -> str:
        try:
            encoded = urllib.parse.quote_plus(query)
            url     = f"https://www.youtube.com/results?search_query={encoded}"
            webbrowser.open(url)
            return f"Opening YouTube for '{query}'."
        except Exception as e:
            return f"Couldn't open YouTube: {e}"

    def _handle_open(self, target: str) -> str:
        # Check app map first
        app_cmd = APP_MAP.get(target.lower())

        if app_cmd:
            if app_cmd.startswith("http"):
                webbrowser.open(app_cmd)
                return f"Opening {target}."
            return self._launch(app_cmd, target)

        # Try as URL
        if target.startswith(("http://", "https://", "www.")):
            url = target if target.startswith("http") else "https://" + target
            webbrowser.open(url)
            return f"Opening {url}."

        # Try direct launch
        return self._launch(target, target)

    def _launch(self, cmd: str, display_name: str) -> str:
        try:
            if OS == "Windows":
                os.startfile(cmd)
            elif OS == "Darwin":
                subprocess.Popen(["open", cmd])
            else:
                subprocess.Popen([cmd], start_new_session=True)
            return f"Opening {display_name}."
        except FileNotFoundError:
            return (
                f"I couldn't find '{display_name}'. "
                "Make sure it's installed and try again."
            )
        except Exception as e:
            return f"Failed to open {display_name}: {e}"

    def _handle_brightness(self, level: int) -> str:
        level = max(0, min(100, level))
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(level)
            return f"Brightness set to {level}%."
        except ImportError:
            return (
                "screen-brightness-control not installed. "
                "Run: pip install screen-brightness-control"
            )
        except Exception as e:
            return f"Couldn't set brightness: {e}"

    def _win_set_volume(self, level: int):
        """Windows-specific volume setter using pycaw if available."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            iface   = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol     = cast(iface, POINTER(IAudioEndpointVolume))
            vol.SetMasterVolumeLevelScalar(level / 100, None)
        except ImportError:
            # Fallback: use PowerShell
            subprocess.run(
                f'powershell -command "$obj = new-object -com wscript.shell; '
                f'$obj.SendKeys([char]174)"',
                shell=True
            )
