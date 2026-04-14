"""
main.py — Manu AI Assistant
Siri-style: invisible, always-on, fully offline.

Run modes:
  python main.py               → Silent background mode (Siri-style) ✓
  python main.py --gui         → Show full GUI window
  python main.py --console     → Console-only (no tray, no GUI)
  python main.py --no-security → Skip password (development)
  python main.py --setup       → Re-run first-time setup wizard
"""

import sys
import logging
import argparse
import threading
import time
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-18s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "manu.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("Manu")

sys.path.insert(0, str(Path(__file__).parent))

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Manu — Local AI Assistant")
parser.add_argument("--gui",         action="store_true", help="Show full GUI window")
parser.add_argument("--console",     action="store_true", help="Console mode (no tray)")
parser.add_argument("--no-security", action="store_true", help="Skip auth (dev mode)")
parser.add_argument("--setup",       action="store_true", help="Re-run first-time setup")
parser.add_argument("--model",       type=str, default=None, help="Override LLM model")
args, _ = parser.parse_known_args()

import config

if args.no_security:
    config.SECURITY_ENABLED = False
if args.model:
    config.LLM_MODEL = args.model

# ── Imports ───────────────────────────────────────────────────────────────────
# Using modular paths (as expected by Siri-mode)
from modules.memory.store            import MemoryStore
from engines.tts_engine              import TTSEngine
from engines.stt_engine              import STTEngine
from modules.commands.dispatcher     import CommandDispatcher
from modules.emotional.state_manager import EmotionalStateManager
from engines.llm_engine              import LLMEngine
from modules.security.auth           import AuthManager
from modules.events.monitor          import EventMonitor


def main():
    log.info("=" * 55)
    log.info("  MANU — Local AI Assistant (Siri Mode)")
    log.info("=" * 55)

    # ── Ensure data dirs (Bootstrapping Legacy Folders) ───────────────────
    for d in ["data/logs", "data/captures", "data/notes", "data/screenshots", 
             "data/security", "data/sounds", "assets"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    # ── Init core modules ────────────────────────────────────────────────
    memory     = MemoryStore(config.DB_PATH)
    tts        = TTSEngine()
    stt        = STTEngine()
    emotional  = EmotionalStateManager(tts)
    llm        = LLMEngine(memory)
    auth       = AuthManager(tts, memory)
    dispatcher = CommandDispatcher(tts=tts, memory=memory,
                                   llm=llm, emotional=emotional)
    monitor    = EventMonitor(emotional, tts, memory)

    # ── Security ─────────────────────────────────────────────────────────
    if config.SECURITY_ENABLED or args.setup:
        authenticated = auth.authenticate()
        if not authenticated:
            tts.speak("Access denied. Shutting down.")
            sys.exit(1)
    
    # ── Session start ─────────────────────────────────────────────────────
    session_id = memory.start_session()

    # ── Background monitor ────────────────────────────────────────────────
    monitor.start()

    # ── Calibrate mic silently ────────────────────────────────────────────
    stt.calibrate_microphone(duration=1.0)

    # ── Startup voice greeting (no window) ────────────────────────────────
    name = memory.get_setting("user_name", "Friend")
    tts.speak(
        f"Hey {name}, Manu is active and listening. "
        f"Just say Hey Manu anytime you need me."
    )

    # ── Choose run mode ───────────────────────────────────────────────────
    if args.gui:
        # Full GUI mode (original behavior)
        try:
            from ui.app_gui import ManuGUI
            gui = ManuGUI(
                on_command_submit=dispatcher.process,
                on_login_submit=auth.verify_password
            )
            emotional.gui = gui
            # dispatcher.gui = gui # If needed
            gui.run()
        except ImportError as e:
            log.error(f"GUI unavailable: {e}")
            _siri_mode(tts, stt, dispatcher, memory, emotional, session_id)
        except Exception as e:
            log.error(f"GUI error: {e}")
            _siri_mode(tts, stt, dispatcher, memory, emotional, session_id)

    elif args.console:
        # Console mode — print + speak, no tray
        _console_loop(tts, stt, dispatcher, memory, emotional, session_id)

    else:
        # DEFAULT: Siri mode — invisible background with tray icon
        _siri_mode(tts, stt, dispatcher, memory, emotional, session_id)


def _siri_mode(tts, stt, dispatcher, memory, emotional, session_id):
    """Run Manu invisibly with system tray icon and always-on wake word."""
    from engines.siri_mode import SiriMode

    siri = SiriMode(
        tts_engine=tts,
        stt_engine=stt,
        dispatcher=dispatcher,
        memory=memory,
        emotional=emotional,
    )
    siri.start()

    # Keep main thread alive (tray runs in daemon thread)
    log.info("Manu running silently. Check system tray. Press Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Keyboard interrupt — shutting down.")
        memory.end_session(session_id)
        tts.speak("Shutting down. Goodbye!")
        siri.stop()


def _console_loop(tts, stt, dispatcher, memory, emotional, session_id):
    """Simple console loop — type or speak commands."""
    from engines.wake_word_engine import WakeWordEngine

    print("\n" + "=" * 50)
    print("  Manu Console Mode - Type or speak 'Hey Manu'")
    print("  Type your command and press Enter, or speak.")
    print("  Type 'quit' to exit.")
    print("=" * 50 + "\n")

    def _on_wake(wake_tts=tts, wake_stt=stt, wake_dispatcher=dispatcher):
        tts.speak("Yes?")
        cmd = stt.listen(timeout=8, phrase_limit=15)
        if cmd:
            print(f"\nYou: {cmd}")
            memory.log_interaction("user", cmd)
            resp = dispatcher.process(cmd)
            if resp:
                tts.speak(resp)
                memory.log_interaction("assistant", resp)
                print(f"Manu: {resp}\n")

    wake_engine = WakeWordEngine(on_detected_callback=_on_wake)
    wake_engine.start()

    try:
        while True:
            try:
                user_input = input("You (type): ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                break

            memory.log_interaction("user", user_input)
            resp = dispatcher.process(user_input)
            if resp:
                tts.speak(resp)
                memory.log_interaction("assistant", resp)
                print(f"Manu: {resp}\n")

    except KeyboardInterrupt:
        pass
    finally:
        wake_engine.stop()
        memory.end_session(session_id)
        tts.speak("Goodbye!")


if __name__ == "__main__":
    main()
