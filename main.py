import os
import threading
import time
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
        # 1. Initialize logic modules
        self.brain = BrainEngine()
        self.speech = SpeechEngine()
        self.audio = AudioEngine(model="base") # Adjust to "tiny" for low-end laptops
        self.commands = CommandEngine()
        self.memory = MemoryManager()
        self.security = SecurityManager()
        self.emotions = EmotionManager()
        
        # 2. Initialize GUI with callbacks
        self.gui = ManuGUI(
            on_command_submit=self.handle_command,
            on_login_submit=self.handle_login
        )
        
        # 3. Start system monitor
        self.monitor = SystemMonitor(self.handle_system_event)
        self.monitor.start()

        # 4. State
        self.is_listening = False
        
    def handle_login(self, password):
        if self.security.verify_password(password):
            self.gui.is_locked = False
            # Start background wake-word listener thread after unlock
            threading.Thread(target=self.wake_word_listener, daemon=True).start()
            return True
        return False

    def handle_system_event(self, event, detail):
        # Update emotions
        self.emotions.update_mood_on_event(event, detail if isinstance(detail, int) else 100)
        
        # Update GUI status
        self.gui.update_status(
            mood_emoji=self.emotions.get_mood_emoji(),
            battery=detail if event in ["battery_low", "charging", "unplugged"] else None
        )
        
        # Determine if Manu should speak proactively
        proactive_msg = self.brain.get_personality_response(event)
        if proactive_msg and not self.gui.is_locked:
            self.gui.update_chat("Manu", proactive_msg)
            self.speech.speak(proactive_msg)

    def handle_command(self, text):
        if self.gui.is_locked:
            return

        # 1. Check for local system/web commands
        response = self.commands.execute_command(text)
        
        if response == "LOCKED":
             self.security.lock_session()
             self.gui.show_lock_screen()
             return

        # 2. If no local command, use LLM
        if response is None:
            context = f"Current mood is {self.emotions.current_mood}."
            response = self.brain.chat(text, context=context)
            # Add personality prefix
            response = self.emotions.get_contextual_prefix() + response

        # 3. Log memory
        self.memory.log_interaction(text, response)
        
        # 4. Speak and display
        self.gui.update_chat("Manu", response)
        self.speech.speak(response)

    def wake_word_listener(self):
        """
        Background listener for 'Hey Manu'.
        """
        while True:
            if not self.gui.is_locked and not self.is_listening:
                try:
                    text = self.audio.listen_and_recognize()
                    if "manu" in text or "star" in text:
                        self.is_listening = True
                        self.gui.update_chat("System", "Listening for your command...")
                        # In real use, we'd trigger command listening here
                        # For now, we'll just indicate detection
                        self.is_listening = False
                except Exception as e:
                    print(f"Listener error: {e}")
            time.sleep(1)

    def run(self):
        self.gui.show_lock_screen()
        self.gui.mainloop()

if __name__ == "__main__":
    assistant = ManuAssistant()
    assistant.run()
