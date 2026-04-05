import os
import webbrowser
import psutil
import subprocess
import datetime
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

class CommandEngine:
    def __init__(self):
        # Initialize Audio for Pycaw
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def execute_command(self, text):
        """
        Interprets text and executes localized system/web actions.
        """
        text = text.lower()
        
        # Web Search/Open
        if "open youtube" in text:
            webbrowser.open("https://www.youtube.com")
            return "Sure! Opening YouTube now."
        elif "open google" in text or "search for" in text:
            query = text.split("search for")[-1].strip() if "search for" in text else ""
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching Google for {query}."
            else:
                webbrowser.open("https://www.google.com")
                return "Opening Google."
        
        # System Actions
        elif "check battery" in text or "battery level" in text:
            battery = psutil.sensors_battery()
            percent = battery.percent
            plugged = "is plugged in" if battery.power_plugged else "is not plugged in"
            return f"Your battery is at {percent}% and {plugged}."
            
        elif "adjust volume" in text or "set volume to" in text:
            try:
                # Find number in text
                level = int([s for s in text.split() if s.isdigit()][0])
                level = max(0, min(100, level))
                self.volume.SetMasterVolumeLevelScalar(level / 100, None)
                return f"Setting volume to {level}%."
            except:
                return "I couldn't understand the volume level."

        elif "set brightness to" in text or "adjust brightness" in text:
            try:
                level = int([s for s in text.split() if s.isdigit()][0])
                sbc.set_brightness(level)
                return f"Setting brightness to {level}%."
            except:
                return "I couldn't set the brightness."

        elif "tell me a joke" in text:
            import random
            jokes = [
                "Why did the web developer walk out of a restaurant? Because of the table layout.",
                "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
                "Why do computers always crash? Because they have too many windows.",
                "What's a programmer's favorite hangout place? The Foo Bar."
            ]
            return random.choice(jokes)

        elif "what's the time" in text or "time now" in text:
            now = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {now}."
            
        elif "open notepad" in text:
            subprocess.Popen(["notepad.exe"])
            return "Opening Notepad for you."
            
        elif "enter sleep mode" in text:
            # We'll actually implement a 'lock' session logic instead of PC sleep
            return "LOCKED" # Signal for main loop to lock up

        else:
            return None # Fallback to LLM chat if no local command matches

if __name__ == "__main__":
    cmd = CommandEngine()
    print(cmd.execute_command("What is the battery status?"))
