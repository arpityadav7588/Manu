import os
import sys
import threading
import time
import logging
import datetime
import argparse
from pathlib import Path

# Manu Core Engines
from engines.brain_engine import BrainEngine
from engines.speech_engine import SpeechEngine
from engines.audio_engine import AudioEngine
from engines.command_engine import CommandEngine

# Manu Modules
from modules.memory_manager import MemoryManager
from modules.emotion_manager import EmotionManager
from modules.security_manager import SecurityManager
from modules.system_monitor import SystemMonitor
from skills.skill_loader import load_skills

# UI
from ui.app_gui import ManuGUI
import config

class ManuAssistant:
    def __init__(self, no_security=False, no_gui=False):
        self.no_security = no_security
        self.no_gui = no_gui
        self.running = True
        self.is_listening = False
        
        # 1. Setup Logging (Upgrade 9)
        self._setup_logging()
        self._bootstrap_folders()
        
        # 2. Initialize Engines/Modules
        self.memory = MemoryManager()
        self.emotions = EmotionManager()
        self.speech = SpeechEngine()
        self.brain = BrainEngine(self.memory)
        self.audio = AudioEngine()
        
        # Skills
        self.skills = load_skills({'tts': self.speech, 'memory': self.memory, 'brain': self.brain})
        self.commands = CommandEngine(self.brain, self.speech, self.memory, self.skills)
        
        # Security
        self.security = SecurityManager(self.speech, self.memory)
        
        # 3. Monitor
        self.monitor = SystemMonitor(self.handle_system_event, self.memory)
        
        # 4. UI
        if not self.no_gui:
            self.gui = ManuGUI(
                on_command_submit=self.handle_command,
                on_login_submit=self.handle_login
            )
        else:
            self.gui = None

    def _setup_logging(self):
        """Task 9: Logging to data/logs/manu_YYYYMMDD.log."""
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        log_file = config.LOGS_DIR / f"manu_{date_str}.log"
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s'
        )
        logging.info("Manu Session Started.")

    def _bootstrap_folders(self):
        """Task 9: Create required directories."""
        for folder in ["logs", "captures", "notes", "screenshots", "security", "sounds"]:
            path = config.DATA_DIR / folder
            path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Main entry point (Upgrade 9)."""
        if self.no_security or not self.security.is_locked:
            self.is_unlocked = True
            if self.gui: self.gui.show_main_ui()
            self._launch_services()
        else:
            self.is_unlocked = False
            self.security.first_run_if_needed()
            if self.gui:
                self.gui.show_lock_screen()
            else:
                print("[!] System Locked. Run with GUI for login or --no-security.")

        if self.gui:
            self.gui.mainloop()
        else:
            # Console only loop
            while self.running:
                cmd = input("Arpit > ")
                self.handle_command(cmd)

    def _launch_services(self):
        """Startup background loops."""
        self.monitor.start()
        threading.Thread(target=self.wake_word_listener, daemon=True).start()

    def handle_login(self, password):
        """Task 9: Successful login with history recall."""
        if self.security.verify_password(password):
            if self.gui: self.gui.show_main_ui()
            
            user_name = self.memory.get_setting("user_name", "Arpit")
            last_msg = self.memory.get_last_user_message()
            
            greeting = f"Welcome back, {user_name}!"
            if last_msg:
                greeting += f" Last time we talked about: '{last_msg[:60]}...'"
            
            self._respond(greeting)
            self._launch_services()
            return True
        return False

    def wake_word_listener(self):
        """Task 9: Listen for 'Manu' and trigger response."""
        while self.running:
            if self.audio.detect_wake_word():
                self.speech.speak("Yes?") # Upgrade 9
                if self.gui: self.gui.update_status("🔴 Listening...")
                
                text = self.audio.listen_for_command(timeout=8)
                if text:
                    self.handle_command(text)
                else:
                    self._respond("I'm sorry, I didn't catch that.")
                
                if self.gui: self.gui.update_status("🟢 System Ready")
            time.sleep(0.1)

    def handle_command(self, text):
        """Task 9: Command routing with SLEEP_MODE check."""
        if not text: return
        logging.info(f"Command: {text}")
        
        # 1. Check Command Engine (regex/system/skills)
        response = self.commands.execute_command(text)
        
        if response == "SLEEP_MODE":
            self.security.lock_session()
            if self.gui: self.gui.show_lock_screen()
            self._respond("Entering sleep mode. I'll keep your data safe.")
            return

        if response == "TELL_JOKE":
            response = self.emotions.react_to_joke_request()

        # 2. Fallback to Brain Engine (LLM)
        if not response:
            if self.gui: self.gui.update_status("🧠 Thinking...")
            response = self.brain.chat(text, self.emotions.current_mood)
            if self.gui: self.gui.update_status("🟢 System Ready")

        self.memory.log_interaction("user", text)
        self._respond(response)

    def handle_system_event(self, event, detail):
        """Task 9: Handle monitor events."""
        logging.info(f"System Event: {event} | {detail}")
        
        if event == "reminder":
            self._respond(f"Here is your reminder: {detail}")
            return

        # Personality reaction via emotion manager
        if event.startswith("battery"):
            react = self.emotions.react_to_battery(detail, True, event == "charging")
            if react: self._respond(react)
        elif event.startswith("internet"):
            react = self.emotions.react_to_internet(event == "internet_connected")
            if react: self._respond(react)
        elif event == "high_cpu":
            self._respond(f"Notice: CPU usage is quite high at {detail}%. I might be a bit slower.")

    def _respond(self, text):
        """Internal helper for GUI + Speech + Logging."""
        if not text: return
        self.memory.log_interaction("assistant", text)
        
        # Emotion prefix & modulation (Upgrade 4/5 logic)
        prefix = self.emotions.get_contextual_prefix()
        rate, volume = self.emotions.get_tts_params()
        
        wrapped_text = f"{prefix} {text}" if prefix else text
        
        if self.gui:
            self.gui.add_message("Manu", wrapped_text)
            self.gui.update_emotion(self.emotions.get_mood_emoji())
        else:
            print(f"Manu > {wrapped_text}")
            
        self.speech.speak(wrapped_text, rate=rate, volume=volume)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manu AI Assistant Upgrade V1.0")
    parser.add_argument("--no-security", action="store_true", help="Skip login/password check")
    parser.add_argument("--no-gui", action="store_true", help="Run in console-only mode")
    args = parser.parse_args()
    
    app = ManuAssistant(no_security=args.no_security, no_gui=args.no_gui)
    app.start()
