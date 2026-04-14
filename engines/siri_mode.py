"""
engines/siri_mode.py
Siri-style invisible operation.
Manu runs silently — no window, no screen switching.
User hears a soft beep when wake word fires, then speaks naturally.
A tiny system tray icon shows Manu is alive.
"""

import logging
import threading
import time
import os
import sys
from pathlib import Path

log = logging.getLogger("Manu.SiriMode")


class SiriMode:
    """
    Orchestrates Siri-style always-on behavior:
      1. Hides all windows / GUI on startup
      2. Shows system tray icon
      3. Starts background wake word detector
      4. On wake word → beep → listen → process → speak → return to sleep
      5. All processing is offline (no internet needed)
    """

    BEEP_ACTIVATE   = "assets/beep_on.wav"   # short activation tone
    BEEP_DEACTIVATE = "assets/beep_off.wav"  # short dismiss tone

    def __init__(self, tts_engine, stt_engine, dispatcher, memory, emotional):
        self.tts        = tts_engine
        self.stt        = stt_engine
        self.dispatcher = dispatcher
        self.memory     = memory
        self.emotional  = emotional

        self._active    = False   # True while processing a command
        self._tray      = None
        self._wake_engine = None

        # Create asset beeps if they don't exist
        self._ensure_beep_files()

    # ── Startup ─────────────────────────────────────────────────────────
    def start(self):
        """
        Entry point — call this from main.py instead of running the GUI.
        Starts tray icon + wake word engine. Does NOT block.
        """
        log.info("Starting Siri Mode (invisible background operation)")

        # Start system tray icon in its own thread
        tray_thread = threading.Thread(
            target=self._run_tray_icon,
            name="ManuTray",
            daemon=True,
        )
        tray_thread.start()

        # Give tray a moment to appear
        time.sleep(0.5)

        # Import WakeWordEngine and wire the callback
        from engines.wake_word_engine import WakeWordEngine
        self._wake_engine = WakeWordEngine(
            on_detected_callback=self._on_wake_word_detected
        )
        self._wake_engine.start()

        log.info("Manu is listening silently. System tray icon active.")

    def stop(self):
        """Shut everything down cleanly."""
        if self._wake_engine:
            self._wake_engine.stop()
        if self._tray:
            self._tray.stop()

    # ── Wake Word Callback ───────────────────────────────────────────────
    def _on_wake_word_detected(self):
        """
        Called from WakeWordEngine when wake word is heard.
        Runs in background thread — safe to call TTS and STT.
        """
        if self._active:
            return   # Already processing — ignore double-trigger

        self._active = True
        log.info("Wake word detected — entering active mode")

        try:
            # 1. Play activation beep
            self._play_beep(self.BEEP_ACTIVATE)

            # 2. Update tray icon to show "listening" state
            self._update_tray_status("👂 Listening...")

            # 3. Listen for command (offline STT)
            self.emotional.set_mood("listening")
            command_text = self.stt.listen(timeout=8, phrase_limit=15)

            if not command_text:
                self._play_beep(self.BEEP_DEACTIVATE)
                self._update_tray_status("🤖 Manu — Active")
                self._active = False
                return

            log.info(f"Command: '{command_text}'")

            # 4. Save to memory
            self.memory.log_interaction("user", command_text)

            # 5. Update tray — thinking
            self._update_tray_status("🤔 Thinking...")
            self.emotional.set_mood("thinking")

            # 6. Dispatch and get response
            response = self.dispatcher.process(command_text)

            # 7. Speak response (offline TTS)
            if response:
                self.tts.speak(response)
                # self.memory.log_interaction("manu", response) # Some bridge modules might handle this

            # 8. Play dismiss beep and return to listening
            self._play_beep(self.BEEP_DEACTIVATE)

        except Exception as e:
            log.error(f"Siri mode command error: {e}", exc_info=True)
            self.tts.speak("I ran into a small issue. I'm still here.")
        finally:
            self._active = False
            self._update_tray_status("🤖 Manu — Listening")
            self.emotional.set_mood("neutral")

    # ── System Tray Icon ─────────────────────────────────────────────────
    def _run_tray_icon(self):
        """Create and run the system tray icon."""
        try:
            import pystray
            from PIL import Image, ImageDraw

            icon_image = self._make_tray_icon_image()

            menu = pystray.Menu(
                pystray.MenuItem("🤖 Manu is Active", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("📋 View Log",    self._open_log),
                pystray.MenuItem("⚙️  Settings",   self._open_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Quit Manu",   self._quit_manu),
            )

            self._tray = pystray.Icon(
                name="Manu",
                icon=icon_image,
                title="🤖 Manu — Listening",
                menu=menu,
            )
            self._tray.run()   # Blocks this thread (correct for pystray)

        except ImportError:
            log.warning(
                "pystray or Pillow not installed — no tray icon. "
                "Install with: pip install pystray Pillow"
            )
        except Exception as e:
            log.error(f"Tray icon error: {e}")

    def _make_tray_icon_image(self):
        """Generate a simple round tray icon programmatically."""
        from PIL import Image, ImageDraw

        size  = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw  = ImageDraw.Draw(image)

        # Purple circle background
        draw.ellipse([0, 0, size, size], fill=(108, 99, 255, 255))

        # White "M" letter
        draw.text((18, 14), "M", fill="white")

        return image

    def _update_tray_status(self, status: str):
        """Update the tray icon tooltip text."""
        try:
            if self._tray:
                self._tray.title = status
        except Exception:
            pass

    def _open_log(self, icon=None, item=None):
        """Open the Manu log file in the default text editor."""
        import subprocess, platform
        log_path = Path("data/logs/manu.log")
        if log_path.exists():
            if platform.system() == "Windows":
                os.startfile(str(log_path))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(log_path)])
            else:
                subprocess.Popen(["xdg-open", str(log_path)])
        else:
            log.info("No log file found yet.")

    def _open_settings(self, icon=None, item=None):
        """Open config.py in notepad/text editor for quick settings edit."""
        import subprocess, platform
        config_path = Path("config.py")
        if platform.system() == "Windows":
            subprocess.Popen(["notepad", str(config_path)])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", "-e", str(config_path)])
        else:
            subprocess.Popen(["xdg-open", str(config_path)])

    def _quit_manu(self, icon=None, item=None):
        """Stop all Manu processes and exit."""
        log.info("User requested quit via tray.")
        self.stop()
        sys.exit(0)

    # ── Beep Sounds ──────────────────────────────────────────────────────
    def _ensure_beep_files(self):
        """Generate simple beep .wav files if they don't exist."""
        assets_dir = Path("assets")
        assets_dir.mkdir(exist_ok=True)

        for filename, frequency, duration_ms in [
            ("beep_on.wav",  880, 150),   # High beep = listening
            ("beep_off.wav", 440, 100),   # Low beep = done
        ]:
            path = assets_dir / filename
            if not path.exists():
                self._generate_beep_wav(path, frequency, duration_ms)

    def _generate_beep_wav(self, path: Path, freq: int, duration_ms: int):
        """Generate a simple sine wave beep .wav file using only stdlib."""
        import wave, struct, math

        sample_rate = 44100
        num_samples = int(sample_rate * duration_ms / 1000)
        amplitude   = 16000

        with wave.open(str(path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for i in range(num_samples):
                # Sine wave with fade-in/out envelope
                envelope = min(i, num_samples - i, 200) / 200
                sample   = int(amplitude * envelope * math.sin(
                    2 * math.pi * freq * i / sample_rate
                ))
                wav_file.writeframes(struct.pack("<h", sample))

        log.debug(f"Generated beep: {path}")

    def _play_beep(self, wav_path: str):
        """Play a .wav beep file (non-blocking)."""
        def _play():
            try:
                import playsound
                playsound.playsound(wav_path, block=True)
            except ImportError:
                try:
                    # Windows fallback
                    import winsound
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                except Exception:
                    pass   # Silent fail — beep is cosmetic
            except Exception as e:
                log.debug(f"Beep play error: {e}")

        threading.Thread(target=_play, daemon=True).start()
