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
from modules.system_monitor import SystemMonitor
from modules.memory_manager import MemoryManager
from modules.security_manager import SecurityManager
from modules.emotion_manager import EmotionManager
from ui.app_gui import ManuGUI

class ManuAssistant:
    def __init__(self):
        print(f"--- Starting {config.MANU_NAME} Assistant ---")
        
        # 1. Init MemoryManager
        self.memory = MemoryManager()
        
        # 2. Init SpeechEngine
        self.speech = SpeechEngine()
        
        # 3. Init EmotionManager(speech)
        self.emotions = EmotionManager(self.speech)
        
        # 4. Init AudioEngine
        self.audio = AudioEngine(model=config.WHISPER_MODEL)
        
        # 5. Init BrainEngine(memory)
        self.brain = BrainEngine(self.memory)
        
        # 6. Init SecurityManager(speech, memory)
        self.security = SecurityManager(self.speech, self.memory)
        
        # 7. Init CommandEngine(memory)
        self.commands = CommandEngine(self.memory)
        
        # 8. Init ManuGUI
        self.gui = ManuGUI(
            on_command_submit=self.handle_command, 
            on_login_submit=self.handle_login
        )
        
        # 9. Init SystemMonitor
        self.monitor = SystemMonitor(callback=self.handle_system_event)
        
        self.is_listening = False
        self.running = True
        self.session_id = None

    def handle_login(self, password):
        """Callback from GUI login."""
        result = self.security.verify_password(password)
        if result:
            self.session_id = self.memory.start_session()
            threading.Thread(target=self._post_login_setup, daemon=True).start()
        return result

    def _post_login_setup(self):
        """Async setup after successful login."""
        # Update user name from memory settings
        config.USER_NAME = self.memory.get_setting("user_name", config.USER_NAME)
        
        # 1. Speak greeting
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        last_msg = self.memory.get_last_interaction()
        welcome_msg = f"{greeting}, {config.USER_NAME}! I'm ready to assist you."
        if last_msg:
            welcome_msg += f" Last time we spoke about: {last_msg[:30]}..."
        
        self.gui.update_chat("Manu", welcome_msg)
        self.speech.speak(welcome_msg)
        
        # 2. Audio calibrate
        self.audio.calibrate()
        
        # 3. Monitor start
        self.monitor.start(self.memory)
        
        # 4. Update GUI status
        self.gui.update_status("🟢 Online & Listening")
        
        # 5. Start wake word loop
        threading.Thread(target=self.wake_word_loop, daemon=True).start()

    def wake_word_loop(self):
        """Always-on wake word detection thread."""
        while self.running and not self.gui.is_locked:
            if not self.is_listening:
                detected = self.audio.detect_wake_word()
                if detected:
                    self.is_listening = True
                    self.gui.update_status("🔴 Listening...")
                    self.speech.speak("Yes?")
                    
                    command_text = self.audio.listen_for_command()
                    if command_text:
                        self.gui.update_chat("You", command_text)
                        self.handle_command(command_text)
                    else:
                        self.speech.speak("I didn't catch that — but I'm still here!")
                    
                    self.is_listening = False
                    self.gui.update_status("🟢 Online & Listening")
            time.sleep(0.5)

    def handle_command(self, text):
        """Process user input from GUI or Voice."""
        if self.gui.is_locked:
            return
            
        self.memory.log_interaction("user", text)
        self.gui.update_status("🤔 Processing...")
        
        # 1. System/Command Engine first
        response = self.commands.execute_command(text)
        
        if response == "LOCKED":
            self.security.lock_session()
            self.gui.show_lock_screen()
            self.memory.end_session(self.session_id, "Session locked by user.")
            self.session_id = None
            return
        
        # 2. Emotion reactions for special intents
        if any(k in text.lower() for k in ["joke", "make me laugh"]):
            self.emotions.set_mood("playful")
            if not response: # If command engine didn't handle joke
                response = self.emotions.react_to_joke()
        elif any(k in text.lower() for k in ["thank", "great job", "awesome"]):
            self.emotions.set_mood("grateful")
            if not response:
                response = self.emotions.react_to_compliment()
        
        # 3. Brain/LLM Fallback
        if response is None:
            self.emotions.set_mood("thinking")
            context = f"User mood hint: {self.emotions.current_mood}."
            response = self.brain.chat(text, context=context)
            if response:
                prefix = self.emotions.get_contextual_prefix()
                response = f"{prefix} {response}"
        
        if response:
            self.memory.log_interaction("manu", response)
            self.gui.update_chat("Manu", response)
            self.speech.speak(response)
        
        self.emotions.set_mood("neutral")
        self.gui.update_status("🟢 Online & Listening", mood_emoji=self.emotions.get_mood_emoji())

    def handle_system_event(self, event, detail):
        """Handle events from SystemMonitor."""
        self.emotions.update_mood_on_event(event, detail if isinstance(detail, int) else 100)
        
        battery_val = detail if event in ["battery_low", "charging", "battery_full"] else None
        self.gui.update_status(
            "🟢 Online & Listening", 
            mood_emoji=self.emotions.get_mood_emoji(),
            battery=battery_val
        )
        
        msg = None
        if event == "reminder":
            msg = f"🔔 Reminder: {detail}"
        else:
            msg = self.brain.get_personality_response(event)
            
        if msg and not self.gui.is_locked:
            self.gui.update_chat("Manu", msg)
            self.speech.speak(msg)

    def shutdown(self):
        """Cleanup on exit."""
        print("\n--- Shutting down Manu Assistant ---")
        self.running = False
        self.monitor.stop()
        if self.session_id:
            summary = self.brain.summarize_session(self.memory.get_recent_interactions(10))
            self.memory.end_session(self.session_id, summary)
        self.speech.speak("Shutting down. See you soon!")
        sys.exit(0)

    def run(self):
        """Start the GUI main loop."""
        try:
            self.gui.show_lock_screen()
            self.gui.root.protocol("WM_DELETE_WINDOW", self.shutdown)
            self.gui.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manu Assistant Launcher")
    parser.add_argument("--no-gui", action="store_true", help="Run in CLI mode (no UI)")
    parser.add_argument("--no-security", action="store_true", help="Disable password lock")
    parser.add_argument("--no-llm", action="store_true", help="Disable Brain engine")
    args = parser.parse_args()
    
    # Apply CLI flags to config overrides (simplified)
    if args.no_security: config.SECURITY_ENABLED = False
    
    manu = ManuAssistant()
    if args.no_security:
        manu.gui.show_main_ui()
        threading.Thread(target=manu._post_login_setup, daemon=True).start()
        
    manu.run()
