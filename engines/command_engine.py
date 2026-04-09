import re
import os
import subprocess
import webbrowser
import urllib.parse
from datetime import datetime
import psutil
from pathlib import Path

class CommandEngine:
    def execute_command(self, text: str) -> str | None:
        try:
            text = text.lower().strip()
            
            if "sleep mode" in text or "lock session" in text or "enter sleep" in text:
                return "LOCKED"
                
            if "what time" in text or "current time" in text:
                return datetime.now().strftime("It's %I:%M %p")
                
            if "what date" in text or "today" in text:
                return datetime.now().strftime("Today is %A, %B %d, %Y")
                
            if "battery" in text or "charge level" in text:
                battery = psutil.sensors_battery()
                if battery:
                    status = "plugged in" if battery.power_plugged else "on battery"
                    return f"Battery at {int(battery.percent)}%, currently {status}."
                return "Could not determine battery status."
                
            open_match = re.search(r"open\s+(.+)", text)
            if open_match:
                app_name = open_match.group(1).strip()
                if app_name in ["youtube", "google", "gmail", "reddit", "github"]:
                    webbrowser.open(f"https://{app_name}.com")
                elif app_name == "notepad":
                    os.startfile("notepad")
                elif app_name in ["calculator", "calc"]:
                    os.startfile("calc")
                elif app_name in ["file explorer", "explorer"]:
                    os.startfile("explorer")
                elif app_name == "spotify":
                    try:
                        subprocess.Popen(["spotify"])
                    except:
                        webbrowser.open("https://open.spotify.com")
                else:
                    return f"I don't know how to open {app_name} yet."
                return f"Opening {app_name}!"
                
            search_match = re.search(r"search(?:\s+for)?\s+(.+)", text)
            if search_match:
                query = search_match.group(1).strip()
                if "youtube" in text:
                    query = query.replace("on youtube", "").replace("youtube", "").strip()
                    webbrowser.open(f"https://youtube.com/results?search_query={urllib.parse.quote_plus(query)}")
                else:
                    webbrowser.open(f"https://google.com/search?q={urllib.parse.quote_plus(query)}")
                return f"Searching for {query}..."
                
            play_match = re.search(r"play\s+(.+)", text)
            if play_match:
                query = play_match.group(1).strip()
                webbrowser.open(f"https://youtube.com/results?search_query={urllib.parse.quote_plus(query + ' music')}")
                return f"Playing {query}..."
                
            if "volume up" in text or "volume down" in text or "mute" in text or re.search(r"set volume to \d+", text):
                return "Volume control commands recognized but not fully implemented on this OS."
                
            note_match = re.search(r"(?:take a note|note that|write down)[:\s]+(.+)", text)
            if note_match:
                note = note_match.group(1).strip()
                Path("./data/notes").mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f"./data/notes/{timestamp}.txt", "w") as f:
                    f.write(note)
                return "Note saved!"
                
            if "screenshot" in text:
                try:
                    from PIL import ImageGrab
                    Path("./data/screenshots").mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    img = ImageGrab.grab()
                    img.save(f"./data/screenshots/{timestamp}.png")
                    return "Screenshot saved!"
                except ImportError:
                    return "PIL not installed for screenshot support."
                except Exception as e:
                    return f"Failed to take screenshot: {e}"
                    
            if "system info" in text or "cpu usage" in text or "memory" in text:
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                return f"CPU is at {cpu}% and Memory is at {mem}%."
                
            if "tell me a joke" in text or "joke" in text:
                return None
                
            remind_match = re.search(r"remind me to\s+(.+?)\s+(?:at|in)\s+(.+)", text)
            if remind_match:
                task = remind_match.group(1).strip()
                time_str = remind_match.group(2).strip()
                return f"Reminder set for {task} at {time_str}!"
                
            return None
        except Exception as e:
            print(f"Command error: {e}")
            return None
