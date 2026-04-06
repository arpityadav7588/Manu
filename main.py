import threading
import time
import sys
import argparse
from datetime import datetime

# Import components
import config
from engines.brain_engine import BrainEngine
from engines.speech_engine import SpeechEngine
from engines.audio_engine import AudioEngine
from engines.command_engine import CommandEngine
from modules.memory_manager import MemoryManager
from modules.security_manager import SecurityManager
from modules.emotion_manager import EmotionManager
from modules.face_emotion import FaceEmotionDetector
from modules.wake_word import WakeWordDetector
from ui.app_gui import ManuGUI
from ui.hologram import HologramWindow

class ManuAssistant:
    def __init__(self):
        print(f"[*] Initializing {config.MANU_NAME} Assistant...")
        
        # Phase 1: Bootstrapping (Task 11)
        self._bootstrap_folders()
        
        self.memory = MemoryManager()
        self.speech = SpeechEngine()
        self.emotions = EmotionManager()
        self.audio = AudioEngine()
        self.brain = BrainEngine(self.memory)
        self.security = SecurityManager(self.speech, self.memory)
        self.commands = CommandEngine(self.speech, self.memory, self.brain)
        self.face_emotion = FaceEmotionDetector(self.speech, self.emotions)
        
        self.hologram = HologramWindow()
        self.gui = ManuGUI(
            on_command_submit=self.handle_command, 
            on_login_submit=self.handle_login,
            hologram=self.hologram
        )
        
        self.wake_detector = WakeWordDetector()
        
        self.running = True
        self.is_listening = False
        
        # Display session summary (Task 3)
        self._show_startup_summary()

    def _bootstrap_folders(self):
        """Ensure all required data directories exist."""
        folders = [
            "logs", "voice_notes", "screenshots", "captures", "security", "skills", "notes"
        ]
        for f in folders:
            path = config.DATA_DIR / f
            path.mkdir(parents=True, exist_ok=True)
            print(f"[*] Directory verified: {f}")

    def _show_startup_summary(self):
        """Show summary of last session on startup."""
        summary = self.memory.summarize_last_session()
        print(f"[*] Last Session Summary: {summary}")

    def handle_login(self, password):
        if self.security.verify_password(password):
            threading.Thread(target=self._launch_sequence, daemon=True).start()
            return True
        return False

    def _launch_sequence(self):
        print("🔓 Unlock successful. Launching...")
        self.hologram.show()
        self.hologram.set_emotion("happy")
        
        name = self.memory.get_setting("user_name", "User")
        msg = f"Welcome back, {name}! How can I help you today?"
        
        self.gui.update_chat("Manu", msg)
        self.speech.speak(msg)
        
        # Start background loops (Task 9)
        self.face_emotion.start()
        self.wake_detector.start(callback=self.on_wake_word)
        threading.Thread(target=self._battery_monitor_loop, daemon=True).start()

    def on_wake_word(self):
        if not self.is_listening and not self.gui.is_locked:
            print("[*] Wake word detected!")
            self.is_listening = True
            self.hologram.set_emotion("listening")
            self.speech.speak("Yes?")
            
            audio_text = self.audio.listen_for_command()
            if audio_text:
                self.gui.update_chat("You (Voice)", audio_text)
                self.handle_command(audio_text)
            
            self.is_listening = False
            self.hologram.set_emotion("neutral")

    def handle_command(self, text):
        if self.gui.is_locked: return
        
        self.hologram.set_emotion("thinking")
        
        # 1. Command Engine (System/Skills)
        response = self.commands.execute_command(text)
        
        if response == "LOCKED":
            self.lock_system()
            return

        # 2. Brain Engine (LLM)
        if not response:
            response = self.brain.chat(text, emotional_context=self.emotions.current_mood)
        
        if response:
            # Phase 1: Habits (Task 3)
            self.memory.log_habit(text[:50])
            
            # Phase 1: Emotion Dynamics (Task 4)
            prefix = self.emotions.get_prefix()
            rate, vol = self.emotions.get_tts_params()
            full_response = f"{prefix} {response}" if prefix else response
            
            self.gui.update_chat("Manu", full_response)
            self.speech.speak(full_response, rate=rate, volume=vol)
            self.memory.log_interaction(text, full_response)
            
        self.hologram.set_emotion(self.emotions.current_mood)
        self.hologram.set_speaking(False)

    def lock_system(self):
        self.security.lock_session()
        self.gui.show_lock_screen()
        self.hologram.set_emotion("sleepy")

    def _battery_monitor_loop(self):
        import psutil
        while self.running:
            batt = psutil.sensors_battery()
            if batt:
                self.gui.update_status(self.emotions.current_mood, batt.percent)
                # Check for personality reaction
                react = self.emotions.react_to_battery_event(batt.percent, batt.power_plugged)
                if react:
                    self.gui.update_chat("Manu", react)
                    self.speech.speak(react)
            time.sleep(60)

    def run(self):
        self.security.first_run_if_needed()
        self.gui.show_lock_screen()
        self.gui.mainloop()

if __name__ == "__main__":
    assistant = ManuAssistant()
    assistant.run()
