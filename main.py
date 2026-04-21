"""
main.py — Manu AI Assistant
Siri-style: invisible, always-on, fully offline.
"""

import argparse
import sys
import logging
import threading
import time
from pathlib import Path
from engines.vision_engine import VisionEngine

# ── Phase 2 Imports ───────────────────────────────────────────────────────────
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-18s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

# ── Core Engine Imports ───────────────────────────────────────────────────────
from engines.brain_engine import BrainEngine
from engines.speech_engine import SpeechEngine
from engines.audio_engine import AudioEngine
from engines.command_engine import CommandEngine
from modules.memory_manager import MemoryManager
from modules.security_manager import SecurityManager
from modules.emotion_manager import EmotionManager
from ui.app_gui import ManuGUI
from modules.system_monitor import SystemMonitor

log = logging.getLogger("Manu")


class ManuAssistant:
    """
    Main controller for the Manu AI Assistant.
    Coordinates speech, hearing, brain (LLM), and system monitoring.
    """

    def __init__(self):
        log.info("Initializing Manu Assistant...")
        
        # ── Engines ───────────────────────────────────────────────────────────
        self.brain    = BrainEngine()
        self.speech   = SpeechEngine()
        self.audio    = AudioEngine(model="base")
        self.commands = CommandEngine()
        
        # ── Managers ──────────────────────────────────────────────────────────
        self.memory   = MemoryManager()
        self.security = SecurityManager()
        self.emotions = EmotionManager()
        self.vision = VisionEngine(self.speech, self.emotions, self.memory)
        
        # ── UI & Monitoring ───────────────────────────────────────────────────
        self.gui      = ManuGUI(
            on_command_submit=self.handle_command,
            on_login_submit=self.handle_login
        )
        self.monitor  = SystemMonitor(self.handle_system_event)
        self.monitor.start()
        self.vision.start()
        
        self.is_listening = False
        log.info("Manu initialization complete.")

    def handle_login(self, password):
        """Handle auth from GUI."""
        success = self.security.verify_password(password)
        if success:
            log.info("Access granted.")
            threading.Thread(target=self.wake_word_listener, daemon=True).start()
            return True
        log.warning("Access denied.")
        return False

    def handle_system_event(self, event, detail):
        """Callback for SystemMonitor."""
        log.info(f"System Event: {event} ({detail})")
        # Route to emotions or voice alerts as needed
        self.emotions.process_event(event, detail)

    def handle_command(self, text):
        """Main command processor."""
        if not text:
            return
            
        log.info(f"Processing command: {text}")
        response = self.commands.execute(text, context={"brain": self.brain})
        
        if response:
            self.speech.speak(response)
            return response

        if isinstance(response, str) and response.startswith("SCREEN_READ"):
            # Extract optional question from command code
            parts    = response.split(":", 1)
            question = parts[1] if len(parts) > 1 else "What is on this screen?"
            response = self.vision.read_screen(question)

        elif response == "FACE_CHECK":
            emotion, conf = "unknown", 0.0
            try:
                frame = self.vision._capture_frame()
                if frame is not None:
                    emotion, conf = self.vision._analyze_emotion(frame)
                    mood_comment  = self.emotions.get_vision_response(emotion)
                    response = (
                        f"I detect {emotion} emotion with "
                        f"{int(conf*100)}% confidence. "
                        f"{mood_comment or ''}"
                    ).strip()
                else:
                    response = "I couldn't access the camera right now."
            except Exception as e:
                response = f"Face check failed: {e}"

        elif response == "VISION_STATUS":
            caps     = self.vision.capabilities
            parts    = []
            if caps["emotion_detection"]:
                parts.append("emotion detection via webcam is active")
            else:
                parts.append("emotion detection is offline (install deepface + opencv)")
            if caps["screen_reading"]:
                parts.append("screen reading via LLaVA is available")
            else:
                parts.append("screen reading needs: ollama pull llava")
            response = "My vision capabilities: " + "; ".join(parts) + "."

        elif response == "SWITCH_VOICE":
            self.speech._edge_available = True
            response = (
                f"Switching to neural voice: {self.speech.backend_name}. "
                "This requires an internet connection."
            )

        elif response == "SWITCH_VOICE_OFFLINE":
            self.speech._edge_available = False
            response = "Switched to offline pyttsx3 voice."

    def wake_word_listener(self):
        """
        Background thread: listen for wake word using Whisper-tiny.
        Called after successful login in handle_login().
        This is the GUI-mode wake word loop.
        For full Siri mode (no GUI), use --siri flag.
        """
        from engines.wake_word_engine import WakeWordEngine
        from engines.beep_engine import BeepEngine

        beep   = BeepEngine()
        engine = WakeWordEngine(on_detected=self._on_wake_detected)
        engine.start()

        # Keep thread alive — engine runs in its own daemon thread
        while True:
            time.sleep(1)

    def _on_wake_detected(self):
        """Called by WakeWordEngine when wake word heard in GUI mode."""
        from engines.beep_engine import BeepEngine
        try:
            if self.gui.is_locked:
                return
        except AttributeError:
            # If GUI hasn't fully loaded or handles locking differently
            pass

        BeepEngine().play_activate()
        self.gui.update_chat("System", "Listening...")

        text = self.audio.listen_and_recognize(timeout=8, phrase_limit=15)
        if text:
            self.gui.update_chat("You", text)
            self.handle_command(text)

        BeepEngine().play_deactivate()

    def run(self):
        """Normal GUI launch mode."""
        self.gui.show_lock_screen()
        self.gui.run()  # mainloop


if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="Manu AI Assistant")
    parser.add_argument(
        "--siri",
        action="store_true",
        help="Run invisibly in background (Siri mode, no GUI window)",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Console-only mode (text input, no GUI, no tray)",
    )
    parser.add_argument(
        "--no-security",
        action="store_true",
        help="Skip password login (development mode)",
    )
    args, _ = parser.parse_known_args()

    assistant = ManuAssistant()

    if args.siri:
        # ── SIRI MODE: invisible + always listening ──────────────────
        from engines.siri_mode import SiriMode
        siri = SiriMode(assistant)
        siri.start()
        siri.run_forever()      # Blocks main thread forever

    elif args.console:
        # ── CONSOLE MODE: type commands in terminal ──────────────────
        from engines.wake_word_engine import WakeWordEngine
        from engines.beep_engine      import BeepEngine

        print("\n" + "=" * 50)
        print("  Manu — Console Mode")
        print("  Type a command and press Enter.")
        print("  Or just say 'Hey Manu' (wake word active).")
        print("  Type 'quit' to exit.")
        print("=" * 50 + "\n")

        assistant.audio.calibrate(duration=1.0)
        beep = BeepEngine()

        def _on_wake():
            beep.play_activate()
            print("\n[Wake word detected — speak your command]\n")
            cmd = assistant.audio.listen_and_recognize(timeout=8)
            if cmd:
                print(f"You: {cmd}")
                assistant.handle_command(cmd)
            beep.play_deactivate()

        wwe = WakeWordEngine(on_detected=_on_wake)
        wwe.start()

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                assistant.speech.speak("Goodbye.")
                break
            assistant.handle_command(user_input)

    else:
        # ── NORMAL GUI MODE: original behavior unchanged ─────────────
        assistant.run()
