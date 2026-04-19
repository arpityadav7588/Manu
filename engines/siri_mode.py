"""
engines/siri_mode.py
Orchestrates Manu's invisible Siri-style operation.

Wires together:
  WakeWordEngine → detects "hey manu"
  BeepEngine     → plays activation / deactivation tones
  TrayEngine     → manages system tray icon
  ManuAssistant  → handle_command() for actual processing

Flow every time wake word is heard:
  1. Pause wake detection
  2. Play HIGH beep
  3. Update tray → "listening" (teal)
  4. Call audio.listen_and_recognize() for the command
  5. If something heard → call handle_command(text)
  6. Play LOW beep after response
  7. Update tray → "idle" (purple)
  8. Resume wake detection
"""

import logging
import sys
import time
import threading
from pathlib import Path

log = logging.getLogger("Manu.SiriMode")


class SiriMode:
    """
    Runs Manu invisibly.
    Activated by wake word. Responds via speaker. No screen interaction.
    """

    def __init__(self, assistant):
        """
        assistant: the ManuAssistant instance from main.py
        Gives us access to: assistant.audio, assistant.speech,
                            assistant.handle_command(), assistant.memory
        """
        self._assistant = assistant
        self._muted     = False

        # Import engines
        from engines.wake_word_engine import WakeWordEngine
        from engines.beep_engine      import BeepEngine
        from engines.tray_engine      import TrayEngine

        self._beep = BeepEngine()

        self._wake = WakeWordEngine(
            on_detected=self._on_wake_word_detected,
        )

        self._tray = TrayEngine(
            on_open_gui    = self._open_gui,
            on_quit        = self._quit,
            on_mute_toggle = self._set_mute,
        )

    # ── Startup ───────────────────────────────────────────────────────────────

    def start(self):
        """
        Start all background systems.
        Call this instead of assistant.run() for Siri mode.
        """
        log.info("=" * 55)
        log.info("  Manu — Siri Mode Active")
        log.info("  No window. Say 'Hey Manu' anytime.")
        log.info("  Right-click system tray icon to access menu.")
        log.info("=" * 55)

        # Setup file logging so tray "View Log" works
        self._setup_file_logging()

        # Start tray icon (background thread)
        self._tray.start()
        time.sleep(0.3)   # Give tray time to appear before greeting

        # Calibrate microphone once at startup
        self._assistant.audio.calibrate(duration=1.2)

        # Brief startup greeting (spoken only, no window)
        name = self._assistant.memory.get_setting("user_name", "sir")
        greeting = (
            f"Siri mode active. I'm listening, {name}. "
            f"Just say hey Manu whenever you need me."
        )
        self._assistant.speech.speak_async(greeting)
        self._tray.update_status("🤖 Manu — Listening")

        # Start wake word detection (background thread)
        self._wake.start()

        # Wait for tiny model to load before considering ready
        self._wait_for_wake_ready()

        log.info("Manu is fully operational in Siri mode.")

    def _wait_for_wake_ready(self, timeout: float = 30.0):
        """Block until Whisper-tiny is loaded or timeout reached."""
        start = time.time()
        log.info("Waiting for Whisper-tiny wake model to load...")
        while not self._wake.is_ready:
            if time.time() - start > timeout:
                log.warning("Wake model took too long to load — continuing anyway.")
                break
            time.sleep(0.2)
        if self._wake.is_ready:
            log.info("Wake detection ready. System fully online.")

    def run_forever(self):
        """
        Block the main thread forever while background threads do the work.
        This replaces gui.mainloop() in Siri mode.
        """
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Keyboard interrupt — shutting down Manu.")
            self._quit()

    # ── Wake Word Response ────────────────────────────────────────────────────

    def _on_wake_word_detected(self):
        """
        Called by WakeWordEngine when "hey manu" is heard.
        Runs in WakeWordEngine's background thread.
        Full command processing happens here.
        """
        if self._muted:
            log.debug("Wake word heard but Manu is muted — ignoring.")
            return

        log.info("Wake word detected — entering active mode.")

        # Update tray to show "listening"
        self._tray.update_icon_state("listening")
        self._tray.update_status("👂 Manu — Listening...")

        # Play HIGH activation beep
        self._beep.play_activate()

        # Short pause after beep so user doesn't speak over it
        time.sleep(0.15)

        try:
            # Listen for the actual command (uses base Whisper model — accurate)
            log.info("Listening for command...")
            command_text = self._assistant.audio.listen_and_recognize(
                timeout=8,
                phrase_limit=15,
            )

            if not command_text or not command_text.strip():
                log.info("No command heard after wake word.")
                self._assistant.speech.speak_async(
                    "I didn't catch that. I'm still listening."
                )
                return

            log.info(f"Command received: '{command_text}'")

            # Update tray to show "thinking"
            self._tray.update_icon_state("thinking")
            self._tray.update_status(f"🤔 Processing: {command_text[:40]}...")

            # Route through the existing handle_command() — same as GUI
            self._assistant.handle_command(command_text)

            # Update tray with last command summary
            self._tray.update_status(
                f"✅ Done: {command_text[:35]}{'...' if len(command_text)>35 else ''}"
            )

        except Exception as e:
            log.error(f"Command processing error: {e}", exc_info=True)
            self._assistant.speech.speak_async(
                "I ran into an issue there. Still online — try again."
            )

        finally:
            # Always play deactivation beep and return to idle
            self._beep.play_deactivate()
            self._tray.update_icon_state("idle")
            self._tray.update_status("🤖 Manu — Listening")
            log.info("Command cycle complete. Back to wake word detection.")

    # ── Tray Callbacks ────────────────────────────────────────────────────────

    def _open_gui(self):
        """Launch the Tkinter GUI window on demand from tray menu."""
        log.info("Opening GUI from tray.")
        try:
            # Import and show existing GUI
            import threading
            def _launch():
                try:
                    self._assistant.gui.deiconify()
                except Exception:
                    # GUI wasn't created yet — create it now
                    self._assistant.gui.show_lock_screen()
                    self._assistant.gui.mainloop()

            threading.Thread(target=_launch, daemon=True).start()
        except Exception as e:
            log.error(f"GUI launch failed: {e}")
            self._assistant.speech.speak_async(
                "Couldn't open the GUI window right now."
            )

    def _set_mute(self, muted: bool):
        """Mute or unmute Manu's voice output."""
        self._muted = muted
        state = "muted" if muted else "ready"
        log.info(f"Manu {state}.")
        if not muted:
            self._assistant.speech.speak_async("Unmuted. I'm listening again.")

    def _quit(self):
        """Graceful shutdown."""
        log.info("Shutting down Manu...")
        self._wake.stop()
        self._tray.stop()
        self._assistant.speech.speak_async("Powering down. Goodbye.")
        time.sleep(1.5)   # Let the goodbye speech finish
        sys.exit(0)

    # ── File Logging ──────────────────────────────────────────────────────────

    def _setup_file_logging(self):
        """Add file handler so 'View Log' in tray shows something useful."""
        import logging
        log_dir  = Path("data") / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "manu.log"

        # Only add file handler once
        root_logger = logging.getLogger()
        for h in root_logger.handlers:
            if isinstance(h, logging.FileHandler):
                return   # Already has file handler

        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)-18s] %(levelname)s  %(message)s",
            datefmt="%H:%M:%S",
        ))
        root_logger.addHandler(fh)
        log.info(f"Logging to {log_path}")
